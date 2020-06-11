
import re
from typing import Iterable, Set, Tuple, List, Sequence
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


class UniformParam:
    def __init__(self, _type:str, name:str) -> None:
        valid_types = {
            "int" : ("int", 1, 1),
            "float" : ("float", 1, 1),
            "vec2" : ("float", 2, 2),
            "vec3" : ("float", 3, 4),
            "vec4" : ("float", 4, 4),
            "mat2" : ("float", 8, 4),  # "words" field is prealigned to simplify array rules
            "mat3" : ("float", 12, 4), # "words" field is prealigned to simplify array rules
            "mat4" : ("float", 16, 4),
        }
        if _type in valid_types:
            self.name:str = name
            self.type:str = _type
            self.component:str = valid_types[_type][0]
            self.words:int = valid_types[_type][1]
            self.align:int = valid_types[_type][2]
            self.vector:bool = _type.startswith("vec")
            self.matrix:bool = _type.startswith("mat")
            self.scalar:bool = not (self.vector or self.matrix)
        else:
            raise TypeError("Unsupported uniform interface member type: f{_type}")


class UniformInterface:
    def __init__(self, *params:UniformParam) -> None:
        assert(len(params) > 1)
        def div_up(n:int, d:int)->int:
            return (n + d -1) // d
        def align(offset:int, alignment:int) -> int:
            return div_up(offset, alignment) * alignment
        first = params[0]
        self.layout = [(0, first)]
        offset:int = first.words
        for param in params[1:]:
            offset = align(offset, param.align)
            self.layout.append((offset, param))
            offset += param.words
        assert(len(set([param.name for param in params])) == len(params)) # duplicate names


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
