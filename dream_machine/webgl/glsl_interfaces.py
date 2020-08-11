
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


from ..opengl.glsl_types import *
from ..opengl.glsl_interfaces import GlslStruct
from ..syntax.grammar import PipelineInput, PipelineOutput


class UniformDeclaration(SyntaxExpander):
    template = "uniform 「type」 「name」;"

    def __init__(self, member_name:str, member_type:GlslType):
        SyntaxExpander.__init__(self)
        if type(member_type) in (ScalarType, VectorType, MatrixType):
            self.name = member_name
            self.type = member_type.name
        else:
            raise NotImplementedError("uniform array and or struct fields in shaders")


class UniformInterface(SyntaxExpander):
    template = "「wrapped」"
    def __init__(self, struct: StructType, input: PipelineInput):
        SyntaxExpander.__init__(self)
        members = [m for m in struct.members.items()]
        self.wrapped = [UniformDeclaration(*m) for m in members]


class TextureInterface(SyntaxExpander):
    template = "uniform sampler「mode:str」 「name:str」;"

    def __init__(self, input: PipelineInput):
        SyntaxExpander.__init__(self)
        self.binding_point = input.texture_index
        self.mode = self.sampler_type(input.format.target)
        self.name = input.binding_name

    def sampler_type(self, target:str) -> str:
        if target == "GL_TEXTURE_2D":
            return "2D"
        elif target == "GL_TEXTURE_3D":
            return "3D"
        else:
            assert(target == "GL_TEXTURE_CUBE_MAP")
            return "Cube"


class TargetInterface(SyntaxExpander):
    template = "layout(location = 「index:int」)\n out 「type:str」 「name:str」;"

    def __init__(self, output: Optional[PipelineOutput]):
        SyntaxExpander.__init__(self)
        if output is not None:
            self.index = output.color_index
            self.name = output.texture.name
            self.type = "vec4"
        else:
            self.index = 0
            self.name = "OutColor"
            self.type = "vec4"
