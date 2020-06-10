
from typing import List
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


class ColorClear(SyntaxExpander):
    template="glClearColor(「color」);\nglClear(GL_COLOR_BUFFER_BIT);"
    def __init__(self, red: float, green: float, blue: float, alpha: float=1.0):
        SyntaxExpander.__init__(self)
        self.color = ", ".join(map(str, [red, green, blue, alpha]))


class DepthClear(SyntaxExpander):
    template = "glClearDepth(「depth」);\nglClear(GL_DEPTH_BUFFER_BIT);"


class Capability(SyntaxExpander):
    template = "gl「state_prefix」able(「capability」);"
    def __init__(self, capability: str, state: bool):
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


class WrapCpp(SyntaxExpander):
    template = """「wrapped」"""
