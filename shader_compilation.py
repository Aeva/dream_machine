
import os
from typing import *
from hashlib import md5
from graffeine.templates import SyntaxExpander, external, rewrite


class ShaderHandles(SyntaxExpander):
    template = """
GLuint Shaders[「shader_count」] = { 0 };
GLuint ShaderPrograms[「program_count」] = { 0 };
std::string ShaderPaths[「shader_count」] = {\n「paths」\n};
""".strip()
    indent = ("paths",)


class CompileShader(SyntaxExpander):
    template = "Shaders[「index」] = CompileShader(ShaderPaths[「index」], 「stage」);"
    def __init__(self, index: int, shader):
        SyntaxExpander.__init__(self)
        self.index = index
        self.path = shader.path
        self.stage = shader.stage


class LinkShaders(SyntaxExpander):
    template = """
{
	GLuint Stages[「shader_count」] = { 「shaders」 };
	ShaderPrograms[「index」] = LinkShaders(\"「name」\", &Stages[0], 「shader_count」);
}
""".strip()
    def __init__(self, name: str, index: int, shaders:List[int]):
        SyntaxExpander.__init__(self)
        self.name = name
        self.index = str(index)
        self.shader_count = str(len(shaders))
        self.shaders = ", ".join([f"Shaders[{shader}]" for shader in shaders])


class ChangeProgram(SyntaxExpander):
    template = "glUseProgram(ShaderPrograms[「index」]);"


class ShaderStage:
    """
    Immutable data corresponding roughly to the parameters for the OpenGL API
    calls "glCreateShader" and "glShaderSource".
    """
    def __init__(self, stage: str, path: str, interfaces: list) -> None:
        assert(stage in ["vertex", "fragment"])
        self.path = path
        self.stage = f"GL_{stage.upper()}_SHADER"
        class GlslTransform(SyntaxExpander):
            template = external(path)
        self.src = str(GlslTransform(interfaces))

    def save(self) -> str:
        name = f"{os.path.split(self.path)[-1]}.{md5(str(self).encode()).hexdigest()}.glsl"
        path = os.path.join("generated_shaders", name)
        with open(path, "w") as generated:
            generated.write(self.src)
        return path.encode("unicode_escape").decode("utf8")

    def __str__(self):
        return str((self.path, self.stage, self.src))

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
    paths = ",\n".join([f'"{shader.save()}"' for shader in shaders])
    compiles: List[SyntaxExpander] = solve_shader_compilation(shaders)
    links: List[SyntaxExpander] = solve_shader_linking(shaders, programs)
    return ShaderHandles(shader_count = len(shaders), program_count=len(programs), paths=paths), compiles + links
