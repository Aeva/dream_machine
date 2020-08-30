﻿
# Copyright 2020 Aeva Palecek
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from typing import *
from ..expanders import SyntaxExpander
from ..handy import CAST
from ..syntax.grammar import Texture, Sampler, PipelineInput, Program
from ..syntax.constants import SamplerFilterType


SAMPLER_FILTER_MODES = {
    SamplerFilterType.POINT : "GL_NEAREST",
    SamplerFilterType.LINEAR : "GL_LINEAR",
}


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

    def __init__(self, binding:PipelineInput):
        SyntaxExpander.__init__(self)
        self.texture_unit = binding.texture_index
        self.handle = CAST(Texture, binding.texture).sampler.handle


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
        self.min_filter = SAMPLER_FILTER_MODES[sampler.filters["min"].value]
        self.mag_filter = SAMPLER_FILTER_MODES[sampler.filters["mag"].value]


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
