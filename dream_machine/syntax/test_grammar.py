
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


def test_pipeline_inputs():
    src = """
(sampler PointSampler (min GL_NEAREST) (mag GL_NEAREST))
(format ColorFormat GL_TEXTURE_2D GL_RGBA8 PointSampler)
(texture SomeTexture1 ColorFormat
    (width ScreenWidth)
    (height ScreenHeight))
(texture SomeTexture2 ColorFormat
    (width ScreenWidth)
    (height ScreenHeight))
(struct SomeStruct1
    (vec4 Fnord)
    (float Meep))
(struct SomeStruct2
    (vec4 Moop)
    (float Bloop))
(buffer SomeBuffer1 SomeStruct1)
(buffer SomeBuffer2 SomeStruct2)
(pipeline TestPass
    (vs "vs.glsl")
    (fs "fs.glsl")
    (in SomeBuffer1)
    (in SomeBuffer2)
    (in SomeTexture1)
    (in SomeTexture2))
"""
    env = run(src)
    pipeline = env.pipelines["TestPass"]
    assert(len(pipeline.textures) == 2)
    assert(len(pipeline.uniforms) == 2)
    assert(pipeline.textures[0].is_texture)
    assert(pipeline.textures[1].is_texture)
    assert(not pipeline.textures[0].is_uniform)
    assert(not pipeline.textures[1].is_uniform)
    assert(pipeline.textures[0].texture is not None)
    assert(pipeline.textures[1].texture is not None)
    assert(pipeline.textures[0].buffer is None)
    assert(pipeline.textures[1].buffer is None)
    assert(pipeline.uniforms[0].is_uniform)
    assert(pipeline.uniforms[1].is_uniform)
    assert(not pipeline.uniforms[0].is_texture)
    assert(not pipeline.uniforms[1].is_texture)
    assert(pipeline.uniforms[0].buffer is not None)
    assert(pipeline.uniforms[1].buffer is not None)
    assert(pipeline.uniforms[0].texture is None)
    assert(pipeline.uniforms[1].texture is None)


def test_pipeline_outputs():
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
    (out GBuffer1)
    (out ZBuffer)
    (out GBuffer2))
"""
    env = run(src)
    pipeline = env.pipelines["TestPass"]
    assert(len(pipeline.outputs) == 3)
    assert(pipeline.outputs[0] in pipeline.color_targets)
    assert(pipeline.outputs[2] in pipeline.color_targets)
    assert(pipeline.outputs[1] is pipeline.depth_target)
