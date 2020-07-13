
from ..handy import *
from .tokens import *
from .parser import Parser
from .grammar import *


def run(source:str):
    p = Parser()
    p.reset(source)
    return validate(p)


def test_arithmetic():
    src = """
(sampler WhateverSampler (min GL_LINEAR) (mag GL_LINEAR))
(format WhateverFormat GL_TEXTURE_2D GL_RGBA8 WhateverSampler)
(texture Fnord WhateverFormat
    (width (mul 2 3 4))
    (height (mul (div 1 2) ScreenWidth)))
"""
    env = run(src)
    texture = env.textures["Fnord"]
    assert(texture.width == 2 * 3 * 4)
    assert(type(texture.height) is UnfoldedExpression)
