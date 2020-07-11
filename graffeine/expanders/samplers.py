
from typing import *
from .common import SyntaxExpander
from ..syntax.grammar import Sampler, RendererDrawBind, Program


class SamplerHandles(SyntaxExpander):
    template = "GLuint SamplerHandles[「count」] = { 0 };"


class CreateSamplers(SyntaxExpander):
    template = "glCreateSamplers(「count」, &SamplerHandles[「start」]);"

    def __init__(self, count:int, start:int=0):
        SyntaxExpander.__init__(self, count=count, start=start)


class SamplerIntegerParam(SyntaxExpander):
    template = "glSamplerParameteri(SamplerHandles[「handle」], 「param」, 「value」);"


class SamplerFloatParam(SyntaxExpander):
    template = "glSamplerParameterf(SamplerHandles[「handle」], 「param」, 「value」);"


class BindSampler(SyntaxExpander):
    template = "glBindSampler(「texture_unit」, SamplerHandles[「handle」]);"

    def __init__(self, binding:RendererDrawBind):
        SyntaxExpander.__init__(self)
        self.texture_unit = binding.interface.texture_unit
        self.handle = binding.sampler.handle


class SamplerSetup(SyntaxExpander):
    template = """
{
	// sampler "「name:str」"
	glSamplerParameteri(SamplerHandles[「handle:int」], GL_TEXTURE_MIN_FILTER, 「min_filter:str」);
	glSamplerParameteri(SamplerHandles[「handle:int」], GL_TEXTURE_MAG_FILTER, 「mag_filter:str」);
	glObjectLabel(GL_SAMPLER, SamplerHandles[「handle:int」], -1, \"「name:str」\");
}
""".strip()
    def __init__(self, sampler:Sampler):
        SyntaxExpander.__init__(self)
        self.name = sampler.name
        self.handle = sampler.handle
        self.min_filter = sampler.filters["min"].value
        self.mag_filter = sampler.filters["mag"].value


class SetupSamplers(SyntaxExpander):
    template = """
{
「wrapped」
}
""".strip()
    indent = ("wrapped",)

    def __init__(self, env:Program):
        SyntaxExpander.__init__(self)
        self.wrapped:List[SyntaxExpander] = [CreateSamplers(len(env.samplers))]
        self.wrapped += [SamplerSetup(s) for s in env.samplers.values()]
