
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


from .glsl_types import *
from .textures import GLFormat
from ..syntax.grammar import PipelineInput, PipelineOutput, PipelineSideput, Format
from ..syntax.constants import TextureType


class GlslMember(SyntaxExpander):
    template = "「type」 「name」「array」;"
    def __init__(self, member_name: str, member_type: GlslType):
        SyntaxExpander.__init__(self)
        self.type = member_type.name
        self.name = member_name
        self.array = ""
        if (type(member_type) is ArrayType):
            self.array = f"[{member_type.array_size}]"


class GlslStruct(SyntaxExpander):
    template = "struct 「name」\n{\n「members」\n};"
    indent = ("members",)
    def __init__(self, struct: StructType):
        SyntaxExpander.__init__(self)
        self.name = struct.name
        self.members = [GlslMember(*member) for member in struct.members.items()]


class UniformInterface(SyntaxExpander):
    template = "layout(std140, binding = 「binding_point」)\nuniform 「block_name」\n{\n「members」\n}「instance_name」;"
    indent = ("members",)
    def __init__(self, struct: StructType, input: PipelineInput):
        SyntaxExpander.__init__(self)
        self.block_name = input.binding_name
        self.binding_point = input.uniform_index
        self.members = [GlslMember(*member) for member in struct.members.items()]
        self.instance_name = ""


class TextureInterface(SyntaxExpander):
    template = "layout(binding = 「binding_point」)\nuniform sampler「mode:str」 「name:str」;"

    def __init__(self, input: PipelineInput):
        SyntaxExpander.__init__(self)
        self.binding_point = input.texture_index
        self.mode = self.sampler_type(input.format.target)
        self.name = input.binding_name

    def sampler_type(self, target:TextureType) -> str:
        if target == TextureType.TEXTURE_1D:
            return "1D"
        elif target == TextureType.TEXTURE_2D:
            return "2D"
        elif target == TextureType.TEXTURE_3D:
            return "3D"
        elif target == TextureType.TEXTURE_CUBE_MAP:
            return "Cube"
        elif target == TextureType.BUFFER:
            return "Buffer"
        else:
            raise NotImplementedError(target.name)


class ImageInterface(SyntaxExpander):
    template = "layout(「format:str」, binding = 「unit」)\nuniform image「mode:str」 「name:str」;"

    def __init__(self, sideput: PipelineSideput):
        SyntaxExpander.__init__(self)
        self.format = self.image_format(sideput.format)
        self.unit = sideput.binding_index
        self.mode = self.image_type(sideput.format.target)
        self.name = sideput.resource_name

    def image_type(self, target:TextureType) -> str:
        if target == TextureType.TEXTURE_1D:
            return "1D"
        elif target == TextureType.TEXTURE_2D:
            return "2D"
        elif target == TextureType.TEXTURE_3D:
            return "3D"
        elif target == TextureType.TEXTURE_CUBE_MAP:
            return "Cube"
        elif target == TextureType.BUFFER:
            return "Buffer"
        else:
            raise NotImplementedError(target.name)

    def image_format(self, format:Format):
        return GLFormat(format)[3:].lower()


class TargetInterface(SyntaxExpander):
    template = "layout(location = 「index:int」)\n out 「type:str」 「name:str」;"

    def __init__(self, output: Optional[PipelineOutput]):
        SyntaxExpander.__init__(self)
        if output is not None:
            self.index = output.color_index
            texture = output.texture.shadow_texture or output.texture
            self.name = texture.name
            self.type = "vec4"
        else:
            self.index = 0
            self.name = "OutColor"
            self.type = "vec4"
