
from graffeine.templates import SyntaxExpander, external
from graffeine.build import build


class OpenGLWindow(SyntaxExpander):
    template = external("OpenGL/main.cpp")
    indent = ("initial_setup_hook", "draw_frame_hook")


if __name__ == "__main__":
    program = OpenGLWindow()
    program.window_title = "Hello World!"
    program.window_width = 512
    program.window_height = 512
    program.hint_version_major = 4
    program.hint_version_minor = 2
    program.hint_profile = "GLFW_OPENGL_CORE_PROFILE"
    program.initial_setup_hook = "// test"
    program.draw_frame_hook = "// test"

    with open("generated.cpp", "w", encoding="utf-8") as outfile:
        outfile.write(str(program))

    build("generated.cpp")
