
import re
from typing import Union, Iterable, Set, Tuple, Dict, List, Sequence
from syntax_expanders import *


class ShaderStage:
    """
    Immutable data corresponding roughly to the parameters for the OpenGL API
    calls "glCreateShader" and "glShaderSource".
    """
    def __init__(self, stage: str, path: str) -> None:
        assert(stage in ["vertex", "fragment"])
        self.path = path
        self.stage = f"GL_{stage.upper()}_SHADER"

    def __str__(self):
        return str((self.path, self.stage))

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)

    def __lt__(self, other):
        return str(self) < str(other)


class ShaderProgram:
    """
    This contains a set of ShaderStage objects and a handy name.  The provided
    name is used to fill out debug events, and to identify linker info log
    entries.

    The provided shader stages can be whatever, but there should only be one
    shader per each shader stage type.  Additionally, the stages should form
    a valid pipeline.
    """
    def __init__(self, name: str, *shaders: ShaderStage) -> None:
        self.name = name
        self.shaders = set(shaders)
        self.stages = tuple(sorted(set([shader.stage for shader in self.shaders])))
        self.validate()

    def validate(self) -> None:
        # if this fails, we have multile shaders using the same stage.
        assert(len(self.stages) == len(self.shaders))
        if self.stages.count("GL_COMPUTE_SHADER") > 0:
            # if this fails, we have a mix of compute and non-compute shaders
            # in the program.
            assert(len(self.stages) == 1)


def unique_shaders(programs: List[ShaderProgram]) -> Tuple[ShaderStage, ...]:
    """
    This function takes a list of all ShaderProgram objects to be used, and
    produces a sorted tuple of all unique ShaderStage objects used by the
    programs.
    """
    shaders: Set[ShaderStage] = set()
    for program in programs:
        shaders = shaders.union(program.shaders)
    return tuple(sorted(shaders))


def solve_shaders(programs: List[ShaderProgram]) -> Tuple[ShaderHandles, List[SyntaxExpander]]:
    """
    This function receives a list of all shader programs used by the generated
    program.  This function returns a ShaderHandles expander (which should go
    in the generated program's global scope), and a list of CompileShader and
    LinkShaders expanders (which produce code that should be called after the
    OpenGL context is initialized, but before the shaders are to be used).
    """

    def solve_shader_compilation(shaders: Tuple[ShaderStage,...]):
        return [CompileShader(*args) for args in enumerate(shaders)]

    def solve_shader_linking(shaders: Tuple[ShaderStage,...], programs: List[ShaderProgram]):
        handle_map = {shader:index for index, shader in enumerate(shaders)}
        links = []
        for index, program in enumerate(programs):
            shader_handles = [handle_map[shader] for shader in program.shaders]
            links.append(LinkShaders(program.name, index, shader_handles))
        return links

    shaders = unique_shaders(programs)
    compiles: List[SyntaxExpander] = solve_shader_compilation(shaders)
    links: List[SyntaxExpander] = solve_shader_linking(shaders, programs)
    return ShaderHandles(shader_count = len(shaders), program_count=len(programs)), compiles + links


def splat(index:int , program:ShaderProgram) -> SyntaxExpander:
    """
    Creates a Drawspatch expander corresponding to a draw call of six verts
    which is for producing a full screen draw.
    """
    return Drawspatch(
        name = program.name,
        setup = ChangeProgram(index),
        draw = InstancedDraw(vertices=6, instances=1))


def div_up(n:int, d:int)->int:
    return (n + d -1) // d


def align(offset:int, alignment:int) -> int:
    return div_up(offset, alignment) * alignment


class GlslType:
    def __init__(self, name:str, alignment:int, words:int) -> None:
        self.name = name
        self.alignment = alignment
        self.words = words
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} \"{self.name}\" {self.alignment} {self.words}>"
    def __eq__(self, other):
        return (self.name, self.alignment, self.words) == (other.name, other.alignment, other.words)
    def __hash__(self):
        return (self.name, self.alignment, self.words)


class ScalarType(GlslType):
    def __init__(self, name:str) -> None:
        GlslType.__init__(self, name, 1, 1)


class VectorType(GlslType):
    def __init__(self, name:str, size:int) -> None:
        assert(size > 1)
        assert(size <= 4)
        GlslType.__init__(self, f"{name}{size}", align(size, 2), size)


class ArrayType(GlslType):
    def __init__(self, base:GlslType, size:int) -> None:
        self.array_size = size
        self.item_type = GlslType(base.name, align(base.words, 4), base.alignment)
        GlslType.__init__(self, f"{base.name}", self.item_type.alignment, self.item_type.alignment * size)


class MatrixType(ArrayType):
    def __init__(self, name:str, size:int) -> None:
        assert(size > 1)
        assert(size <= 4)
        ArrayType.__init__(self, VectorType(f"vec{size}", size), size)
        self.name = f"{name}{size}"


class StructType(GlslType):
    def __init__(self, struct_name:str, **members):
        assert(len(members) > 0)
        self.members:Dict[str, GlslType] = members
        alignment = 0
        for name, member in members.items():
            alignment = max(alignment, member.alignment)
        alignment = align(alignment, 4)
        words = 0
        for member in members.values():
            words = align(words, member.alignment) + member.words
        words = align(words, 4)
        GlslType.__init__(self, struct_name, alignment, words)
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} \"{self.name}\" {self.alignment} {self.words} {self.members}>"


class GlslMember(SyntaxExpander):
    template = "「type」 「name」「array」;"
    def __init__(self, member_name:str, member_type):
        SyntaxExpander.__init__(self)
        self.type = member_type.name
        self.name = member_name
        self.array = ""
        if (type(member_type) is ArrayType):
            self.array = f"[{member_type.array_size}]"


class GlslStruct(SyntaxExpander):
    template = "struct 「name」\n{\n「members」\n};"
    indent = ("members",)
    def __init__(self, struct:StructType):
        SyntaxExpander.__init__(self)
        self.name = struct.name
        self.members = [GlslMember(*member) for member in struct.members.items()]


BuiltinTypes = {
    "bool" : ScalarType("bool"),
    "int" : ScalarType("int"),
    "uint" : ScalarType("uint"),
    "float" : ScalarType("float"),
    "bvec2" : VectorType("bvec", 2),
    "bvec3" : VectorType("bvec", 3),
    "bvec4" : VectorType("bvec", 4),
    "ivec2" : VectorType("ivec", 2),
    "ivec3" : VectorType("ivec", 3),
    "ivec4" : VectorType("ivec", 4),
    "uvec2" : VectorType("uvec", 2),
    "uvec3" : VectorType("uvec", 3),
    "uvec4" : VectorType("uvec", 4),
    "vec2" : VectorType("vec", 2),
    "vec3" : VectorType("vec", 3),
    "vec4" : VectorType("vec", 4),
    "mat2" : MatrixType("mat", 2),
    "mat3" : MatrixType("mat", 3),
    "mat4" : MatrixType("mat", 4),
}


TestStruct = StructType(
    "Fnord",
    eggs = BuiltinTypes["bvec3"],
    cheese = BuiltinTypes["float"],
    butter = BuiltinTypes["ivec2"],
    milk = BuiltinTypes["mat3"],
    kale = BuiltinTypes["bool"],
    oranges = ArrayType(BuiltinTypes["vec3"], 3),
    lemons = BuiltinTypes["int"])


TestStruct2 = StructType(
    "Meep",
    wat = TestStruct,
    fhqwhgads = ArrayType(TestStruct, 2))


print(GlslStruct(TestStruct))
print(GlslStruct(TestStruct2))


from graffeine.templates import indent
def member_offsets(struct:StructType, offset = 0) -> None:
    fields = ""
    for name, _type in struct.members.items():
        aligned = align(offset, _type.alignment)
        padding = aligned - offset
        if padding > 0:
            fields += f"[{offset}:{offset + padding - 1}] [alignment]\n"
        offset = aligned
        fields += f"[{offset}:{offset + _type.words - 1}] "
        if type(_type) is StructType:
            fields += member_offsets(_type) + "\n"
        elif type(_type) is ArrayType:
            fields += str(GlslMember(name, _type)) + "\n"
        else:
            fields += str(GlslMember(name, _type)) + "\n"
        offset += _type.words
    if offset < struct.words:
        padding = struct.words - offset
        fields += f"[{offset}:{offset + padding - 1}] [padding]\n"
    fields = indent(fields)
    return f"struct {struct.name}\n{{\n{fields}}};"

print()
print("------------------------------------")
print("--------- member offsests ----------")
print("------------------------------------")
print(member_offsets(TestStruct))
print(member_offsets(TestStruct2))


if __name__ == "__main__":
    shader_programs = [
        ShaderProgram("draw red", ShaderStage("vertex", "shaders/splat.vs.glsl"), ShaderStage("fragment", "shaders/red.fs.glsl")),
        ShaderProgram("draw blue", ShaderStage("vertex", "shaders/splat.vs.glsl"), ShaderStage("fragment", "shaders/blue.fs.glsl"))
    ]
    shader_handles, build_shaders = solve_shaders(shader_programs)

    # expressions to expand into the global scope hook
    globals:List[SyntaxExpander] = \
    [
        shader_handles
    ]

    # expressions to be called after GL is intialized but before rendering starts
    setup:List[SyntaxExpander] = \
    [
        DefaultVAO(),
        Capability("GL_DEPTH_TEST", False),
        Capability("GL_CULL_FACE", False),
        WrapCpp([
            "glClipControl(GL_LOWER_LEFT, GL_NEGATIVE_ONE_TO_ONE);",
            "glDepthRange(1.0, 0.0);",
            "glFrontFace(GL_CCW);"
        ]),
    ]
    setup += build_shaders

    # expressions to be called every frame to draw
    render:List[SyntaxExpander] = \
    [
        ColorClear(0.5, 0.5, 0.5),
        DepthClear(0.0),
    ]
    render +=  list(map(lambda x: splat(*x), enumerate(shader_programs)))

    # generate the program
    program = OpenGLWindow()
    program.window_title = "Hello World!"
    program.window_width = 512
    program.window_height = 512
    program.hint_version_major = 4
    program.hint_version_minor = 2
    program.hint_profile = "GLFW_OPENGL_CORE_PROFILE"
    program.globals = globals
    program.initial_setup_hook = setup
    program.draw_frame_hook = render

    with open("generated.cpp", "w", encoding="utf-8") as outfile:
        outfile.write(str(program))

    build("generated.cpp", "generated.exe")
