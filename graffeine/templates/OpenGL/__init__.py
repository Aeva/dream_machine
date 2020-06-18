
from ..import *

from .buffers import *
from .glsl_types import *
from .shaders import *
from .drawspatch import *


class OpenGLWindow(SyntaxExpander):
    template = external("OpenGL/main.cpp")
    indent = ("initial_setup_hook", "draw_frame_hook", "renderers", "structs", "uploaders")

