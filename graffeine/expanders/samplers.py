
from .common import SyntaxExpander
from ..syntax.grammar import Sampler


class SamplerHandles(SyntaxExpander):
    template = "GLuint SamplerHandles[「count」] = { 0 };"


class CreateSamplers(SyntaxExpander):
    template = "glCreateSamplers(「count」, &SamplerHandles[「handle」]);"


class SamplerIntegerParam(SyntaxExpander):
    template = "glSamplerParameteri(SamplerHandles[「handle」], 「param」, 「value」);"


class SamplerFloatParam(SyntaxExpander):
    template = "glSamplerParameterf(SamplerHandles[「handle」], 「param」, 「value」);"


class BindSampler(SyntaxExpander):
    template = "glBindSampler(「texture_unit」, SamplerHandles[「handle」]);"


class SamplerSetup(SyntaxExpander):
    template = """
{
	// Setup sampler "「name」"
	glSamplerParameteri(SamplerHandles[「handle」], GL_TEXTURE_MIN_FILTER, 「min_filter」);
	glSamplerParameteri(SamplerHandles[「handle」], GL_TEXTURE_MAG_FILTER, 「mag_filter」);
}
""".strip()
    def __init__(self, handle:int, sampler:Sampler):
        SyntaxExpander.__init__(self)
        self.name = sampler.name
        self.handle = handle
        self.min_filter = sampler.filters["min"].value
        self.mag_filter = sampler.filters["mag"].value
