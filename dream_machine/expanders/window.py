
from .common import SyntaxExpander, external


class OpenGLWindow(SyntaxExpander):
    template = external("main.cpp")
    indent = ("initial_setup_hook", "resize_hook", "draw_frame_hook", "renderers", "structs", "uploaders")
