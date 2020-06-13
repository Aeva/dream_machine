
from typing import *
from graffeine.templates import SyntaxExpander, external


class OpenGLWindow(SyntaxExpander):
    template = external("OpenGL/main.cpp")
    indent = ("initial_setup_hook", "draw_frame_hook", "structs", "uploaders")


class WrapCpp(SyntaxExpander):
    template = """「wrapped」"""
