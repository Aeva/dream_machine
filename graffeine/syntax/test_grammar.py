
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


def test_render_targets():
    src = """
(sampler PointSampler (min GL_NEAREST) (mag GL_NEAREST))
(format ColorFormat GL_TEXTURE_2D GL_RGBA8 PointSampler)
(format DepthFormat GL_TEXTURE_2D GL_DEPTH_COMPONENT32F PointSampler)
(texture GBuffer1 ColorFormat
    (width ScreenWidth)
    (height ScreenHeight))
(texture GBuffer2 ColorFormat
    (width ScreenWidth)
    (height ScreenHeight))
(texture ZBuffer DepthFormat
    (width ScreenWidth)
    (height ScreenHeight))
(pipeline TestPass
	(vs "vs.glsl")
	(fs "fs.glsl")
	(out GBuffer1 ZBuffer GBuffer2))
"""
    env = run(src)
