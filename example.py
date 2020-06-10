
from graffeine.templates import SyntaxExpander, external
from graffeine.build import build


class OpenGLWindow(SyntaxExpander):
    template = external("OpenGL/main.cpp")
    indent = ("initial_setup_hook", "draw_frame_hook")


class ShaderHandles(SyntaxExpander):
    template = """
GLuint Shaders[「shader_count」] = { 0 };
GLuint ShaderPrograms[「program_count」] = { 0 };
""".strip()


class CompileShader(SyntaxExpander):
    template = "Shaders[「index」] = CompileShader(\"「path」\", 「stage」);"


class LinkShaders(SyntaxExpander):
    template = """
{
	GLuint Stages[「shader_count」] = { 「shaders」 };
	ShaderPrograms[「index」] = LinkShaders(\"「name」\", &Stages[0], 「shader_count」);
}
""".strip()
    def __init__(self, name, index, shaders):
        SyntaxExpander.__init__(self)
        self.name = name
        self.index = str(index)
        self.shader_count = str(len(shaders))
        self.shaders = ", ".join([f"Shaders[{shader}]" for shader in shaders])


class ChangeProgram(SyntaxExpander):
    template = "glUseProgram(ShaderPrograms[「index」]);"


class ColorClear(SyntaxExpander):
    template="glClearColor(「color」);\nglClear(GL_COLOR_BUFFER_BIT);"
    def __init__(self, red, green, blue, alpha=1.0):
        SyntaxExpander.__init__(self)
        self.color = ", ".join(map(str, [red, green, blue, alpha]))


class DepthClear(SyntaxExpander):
    template = "glClearDepth(「depth」);\nglClear(GL_DEPTH_BUFFER_BIT);"


class Capability(SyntaxExpander):
    template = "gl「state_prefix」able(「capability」);"
    def __init__(self, capability, state):
        SyntaxExpander.__init__(self)
        self.state_prefix = "En" if state else "Dis"
        self.capability = capability


class DefaultVAO(SyntaxExpander):
    template = """
{
	GLuint vao;
	glGenVertexArrays(1, &vao);
	glBindVertexArray(vao);
}
""".strip()


class InstancedDraw(SyntaxExpander):
    template = "glDrawArraysInstanced(GL_TRIANGLES, 0, 「vertices」, 「instances」);"


class Drawspatch(SyntaxExpander):
    template = """
{
	glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "「name」");
	「setup」
	「draw」
	glPopDebugGroup();
}
""".strip()


class ShaderProgram:
    accumulated_shaders = set()
    def __init__(self, name, **shader):
        self.name = name
        self.shaders = []
        for stage, path in shader.items():
            assert(stage in ["vertex", "fragment"])
            shader = (path, f"GL_{stage.upper()}_SHADER")
            self.accumulated_shaders.add(shader)
            self.shaders.append(shader)
        self.shaders.sort()


def solve_shader_compilation():
    all_shaders = sorted(ShaderProgram.accumulated_shaders)
    return [CompileShader(index = index, path = source[0], stage = source[1]) for index, source in enumerate(all_shaders)]


def solve_shader_linking(programs):
    all_shaders = {source:index for index, source in enumerate(sorted(ShaderProgram.accumulated_shaders))}
    links = []
    for index, program in enumerate(programs):
        shaders = [all_shaders[shader] for shader in program.shaders]
        links.append(LinkShaders(program.name, index, shaders))
    return links


def splat(index, program):
    return Drawspatch(
        name = program.name,
        setup = ChangeProgram(index),
        draw = InstancedDraw(vertices=6, instances=1))


if __name__ == "__main__":
    shader_programs = [
        ShaderProgram("draw red", vertex="splat.vs.glsl", fragment="red.fs.glsl"),
        ShaderProgram("draw blue", vertex="splat.vs.glsl", fragment="blue.fs.glsl"),
    ]
    shader_compiles = solve_shader_compilation()
    shader_links = solve_shader_linking(shader_programs)

    program = OpenGLWindow()
    program.window_title = "Hello World!"
    program.window_width = 512
    program.window_height = 512
    program.hint_version_major = 4
    program.hint_version_minor = 2
    program.hint_profile = "GLFW_OPENGL_CORE_PROFILE"
    program.globals = \
    [
        ShaderHandles(shader_count = len(ShaderProgram.accumulated_shaders), program_count=len(shader_programs))
    ]

    program.initial_setup_hook = \
        shader_compiles + \
        shader_links + \
    [
        DefaultVAO(),
        Capability("GL_DEPTH_TEST", False),
        Capability("GL_CULL_FACE", False),
"""
glClipControl(GL_LOWER_LEFT, GL_NEGATIVE_ONE_TO_ONE);
glDepthRange(1.0, 0.0);
glFrontFace(GL_CCW);
""".strip()
    ]

    program.draw_frame_hook = [
        ColorClear(0.5, 0.5, 0.5),
        DepthClear(0.0),
    ] + list(map(lambda x: splat(*x), enumerate(shader_programs)))

    with open("generated.cpp", "w", encoding="utf-8") as outfile:
        outfile.write(str(program))

    build("generated.cpp", "generated.exe")
