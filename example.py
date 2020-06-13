
import re
from typing import *
from misc import *
from drawing import *
from shader_compilation import *
from graffeine.build import build


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
        self.item_type = base
        self.item_type.words = align(base.words, 4)
        self.item_type.alignment = base.alignment
        GlslType.__init__(self, f"{base.name}", self.item_type.alignment, self.item_type.words * size)


class MatrixType(ArrayType):
    def __init__(self, name:str, size:int) -> None:
        assert(size > 1)
        assert(size <= 4)
        ArrayType.__init__(self, VectorType(f"vec", size), size)
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


class BufferHandle(SyntaxExpander):
    template = "GLuint BufferHandles[「count」] = { 0 };"


class CreateBuffers(SyntaxExpander):
    template = "glCreateBuffers(「count」, &BufferHandles[「handle」]);"


class DeleteBuffers(SyntaxExpander):
    template = "glCreateBuffers(「count」, &BufferHandles[「handle」]);"


class BufferStorage(SyntaxExpander):
    template = "glNamedBufferStorage(「handle」, 「bytes」, nullptr, GL_DYNAMIC_STORAGE_BIT | GL_MAP_WRITE_BIT);"


class ResizeBuffer(SyntaxExpander):
    template = "「wrapped」"
    def __init__(self, handle, bytes):
        self.wrapped = [
            DeleteBuffers(handle=handle, count=1),
            CreateBuffers(handle=handle, count=1), 
            BufferStorage(handle=handle, bytes=bytes)
        ]


class RealignCopy(SyntaxExpander):
    template = "Reflow<「upload_type」>(Mapped, 「offset」, Data.「field」);"

    def __init__(self, upload_type, offset, field):
        SyntaxExpander.__init__(self)
        if upload_type in ["int", "bool"]:
            upload_type = f"_{upload_type}"
        while len(upload_type) < 5:
            upload_type = f" {upload_type}"
        self.upload_type = upload_type
        self.offset = offset
        self.field = field


class Comment(SyntaxExpander):
    template = """
/*
「wrapped」
*/
""".strip()
    indent = ("wrapped",)


def solve_array_reflow(array: ArrayType, offset: int, base: str) -> list:
    copies = []
    if type(array.item_type) in [ScalarType, VectorType]:
        for i in range(array.array_size):
            field = f"{base}[{i}]"
            copies.append(RealignCopy(array.item_type.name, offset, field))
            offset += array.item_type.words
    elif type(array.item_type) in [MatrixType, ArrayType]:
        for i in range(array.array_size):
            field = f"{base}[{i}]"
            copies += solve_array_reflow(array.item_type, offset, field)
            offset += array.item_type.words
    elif type(array.item_type) is StructType:
        for i in range(array.array_size):
            field = f"{base}[{i}]."
            copies += solve_struct_reflow(array.item_type, offset, field)
            offset += array.item_type.words
    return copies


def solve_struct_reflow(struct: StructType, offset = 0, base = "") -> list:
    copies = []
    for member_name, member_type in struct.members.items():
        offset = align(offset, member_type.alignment)
        if type(member_type) in [ScalarType, VectorType]:
            field = f"{base}{member_name}"
            copies.append(RealignCopy(member_type.name, offset, field))
            offset += member_type.words
        elif type(member_type) in [MatrixType, ArrayType]:
            field = f"{base}{member_name}"
            copies += solve_array_reflow(member_type, offset, field)
            offset = align(offset + member_type.words, member_type.alignment)
        elif type(member_type) is StructType:
            field = f"{base}{member_name}."
            copies += solve_struct_reflow(member_type, offset, field)
            offset = align(offset + member_type.words, member_type.alignment)
    return copies


class BufferUpload(SyntaxExpander):
    template = """
void 「struct_name」 (GLuint Handle, Glsl::「struct_name」& Data)
{
	char* Mapped = (char*)glMapNamedBufferRange(Handle, 0, 「bytes」, GL_MAP_WRITE_BIT | GL_MAP_INVALIDATE_BUFFER_BIT );
「reflow」
	glUnmapNamedBuffer(Handle);
}
""".strip()
    indent = ("reflow",)
    def __init__(self, struct:StructType):
        SyntaxExpander.__init__(self)
        self.struct_name = struct.name
        self.bytes = struct.words
        self.reflow = solve_struct_reflow(struct)


class TestUpload(SyntaxExpander):
    template = """
{
	Glsl::「struct_name」 TestUpload = { 0 };
	Upload::「struct_name」 (「handle」, TestUpload);
}
""".strip()



if __name__ == "__main__":
    shader_programs = [
        ShaderProgram("draw red", ShaderStage("vertex", "shaders/splat.vs.glsl"), ShaderStage("fragment", "shaders/red.fs.glsl")),
        ShaderProgram("draw blue", ShaderStage("vertex", "shaders/splat.vs.glsl"), ShaderStage("fragment", "shaders/blue.fs.glsl"))
    ]
    shader_handles, build_shaders = solve_shaders(shader_programs)

    struct_defs = (TestStruct, TestStruct2)
    structs = [GlslStruct(struct) for struct in struct_defs]

    # expressions to expand into the global scope hook
    globals:List[SyntaxExpander] = \
    [
        shader_handles,
        BufferHandle(len(struct_defs)),
    ]
    uploaders = [BufferUpload(struct) for struct in struct_defs]

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
        CreateBuffers(handle=0, count=len(struct_defs)),
    ]
    setup += build_shaders
    setup += [BufferStorage(handle=i, bytes=struct.words) for i, struct in enumerate(struct_defs)]
    setup += [TestUpload(handle = i, struct_name = struct.name) for i, struct in enumerate(struct_defs)]

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
    program.structs = structs
    program.globals = globals
    program.uploaders = uploaders
    program.initial_setup_hook = setup
    program.draw_frame_hook = render

    with open("generated.cpp", "w", encoding="utf-8") as outfile:
        outfile.write(str(program))

    build("generated.cpp", "generated.exe")
