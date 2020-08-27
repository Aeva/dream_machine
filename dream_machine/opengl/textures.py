
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
from enum import IntEnum
from ..expanders import SyntaxExpander
from .cpp_expressions import solve_expression
from ..handy import CAST
from ..syntax.grammar import Texture, Format, TextureDimension, PipelineInput, Program


class InternalFormats(IntEnum):
    """
    The values here are used to map to TextureFormats in dream_machine/syntax/constants.py.
    """

    GL_RGBA32F = 2
    GL_RGBA32UI = 3
    GL_RGBA32I = 4

    GL_RGB32F = 6
    GL_RGB32UI = 7
    GL_RGB32I = 8

    GL_RGBA16F = 10
    GL_RGBA16 = 11
    GL_RGBA16UI = 12
    GL_RGBA16I = 14

    GL_RG32F =  16
    GL_RG32UI = 17
    GL_RG32I = 18

    GL_RGB10_A2 = 24
    GL_RGB10_A2UI = 25

    GL_R11F_G11F_B10F = 26

    GL_RGBA8 = 28
    GL_RGBA8UI = 30
    GL_RGBA8_SNORM = 31
    GL_RGBA8I = 32

    GL_RG16F = 34
    GL_RG16 = 35
    GL_RG16UI = 36
    GL_RG16_SNORM = 37
    GL_RG16I = 38

    GL_DEPTH_COMPONENT32F = 40
    GL_R32F = 41
    GL_R32UI = 42
    GL_R32I = 43

    GL_R8 = 49
    GL_R8UI = 50
    GL_R8_SNORM = 51
    GL_R8I = 52

    GL_R16F = 54
    GL_DEPTH_COMPONENT16 = 55
    GL_R16 = 56
    GL_R16UI = 57
    GL_R16_SNORM = 58
    GL_R16I = 59

    GL_RG8 = 61
    GL_RG8UI = 62
    GL_RG8_SNORM = 63
    GL_RG8I = 64


def GLFormat(format:Format):
    generic:TextureFormat = format.format
    try:
        return InternalFormats(generic).name
    except ValueError:
        format.error(f'Texture format not supported by the OpenGL backend: "{generic.name}"')


class TextureHandles(SyntaxExpander):
    template = "GLuint TextureHandles[「count:int」] = { 0 };"


class ClearTexture(SyntaxExpander):
    template = """
{
	const float ClearColor[] = {「red」, 「green」, 「blue」, 「alpha」};
	glClearTexImage(TextureHandles[「handle:int」], 0, 「format:str」, GL_FLOAT, &ClearColor[0]);
}
""".strip();

    def __init__(self, texture:Texture):
        SyntaxExpander.__init__(self)
        self.handle = texture.handle
        self.format = GLFormat(texture.format)
        self.red, self.green, self.blue, self.alpha = texture.clear.channels


class PngTextureSetup(SyntaxExpander):
    template = """
{
	// texture "「name:str」"
	ImageData Image = ReadPng("「src:TextureSrc」");
	glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[「handle:int」]);
	glTextureStorage2D(TextureHandles[「handle:int」], 1, 「format:str」, Image.Width, Image.Height);
	glObjectLabel(GL_TEXTURE, TextureHandles[「handle:int」], -1, \"「name:str」\");
	glTextureSubImage2D(TextureHandles[「handle:int」], 0, 0, 0, Image.Width, Image.Height, GL_RGBA, GL_UNSIGNED_BYTE, Image.Data.data());
}
""".strip()

    def __init__(self, texture:Texture):
        SyntaxExpander.__init__(self)
        self.name = texture.name
        self.handle = texture.handle
        self.format = GLFormat(texture.format)
        self.src = texture.src


class Texture2DSetup(SyntaxExpander):
    template = """
{
	// texture "「name:str」"
	glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[「handle:int」]);
	glTextureStorage2D(TextureHandles[「handle:int」], 1, 「format:str」, (GLsizei)「width」, (GLsizei)「height」);
	glObjectLabel(GL_TEXTURE, TextureHandles[「handle:int」], -1, \"「name:str」\");
}
""".strip()

    def __init__(self, texture:Texture):
        SyntaxExpander.__init__(self)
        assert(texture.format.target == "GL_TEXTURE_2D")
        self.name = texture.name
        self.handle = texture.handle
        self.format = GLFormat(texture.format)
        self.width = solve_expression(texture.width)
        self.height = solve_expression(texture.height)


class Texture3DSetup(SyntaxExpander):
    template = """
{
	// texture "「name:str」"
	glCreateTextures(GL_TEXTURE_3D, 1, &TextureHandles[「handle:int」]);
	glTextureStorage3D(TextureHandles[「handle:int」], 1, 「format:str」, (GLsizei)「width」, (GLsizei)「height」, (GLsizei)「depth」);
	glObjectLabel(GL_TEXTURE, TextureHandles[「handle:int」], -1, \"「name:str」\");
}
""".strip()

    def __init__(self, texture:Texture):
        SyntaxExpander.__init__(self)
        assert(texture.format.target == "GL_TEXTURE_3D")
        self.name = texture.name
        self.handle = texture.handle
        self.format = GLFormat(texture.format)
        self.width = solve_expression(texture.width)
        self.height = solve_expression(texture.height)
        self.depth = solve_expression(texture.depth)


class ResizeTexture2D(Texture2DSetup):
    template = """
{
	// resize texture "「name:str」"
	glDeleteTextures(1, &TextureHandles[「handle:int」]);
	glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[「handle:int」]);
	glTextureStorage2D(TextureHandles[「handle:int」], 1, 「format:str」, (GLsizei)「width」, (GLsizei)「height」);
	glObjectLabel(GL_TEXTURE, TextureHandles[「handle:int」], -1, \"「name:str」\");
}
""".strip()


class ResizeTexture3D(Texture3DSetup):
    template = """
{
	// resize texture "「name:str」"
	glDeleteTextures(1, &TextureHandles[「handle:int」]);
	glCreateTextures(GL_TEXTURE_3D, 1, &TextureHandles[「handle:int」]);
	glTextureStorage3D(TextureHandles[「handle:int」], 1, 「format:str」, (GLsizei)「width」, (GLsizei)「height」, (GLsizei)「depth」);
	glObjectLabel(GL_TEXTURE, TextureHandles[「handle:int」], -1, \"「name:str」\");
}
""".strip()


def ResizeTexture(texture:Texture) -> SyntaxExpander:
    if texture.format.target == "GL_TEXTURE_2D":
        return ResizeTexture2D(texture)
    else:
        assert(texture.format.target == "GL_TEXTURE_3D")
        return ResizeTexture3D(texture)


class BindTexture(SyntaxExpander):
    template = "glBindTextureUnit(「texture_unit」, TextureHandles[「handle」]);"

    def __init__(self, binding:PipelineInput):
        SyntaxExpander.__init__(self)
        self.texture_unit = binding.texture_index
        self.handle = CAST(Texture, binding.texture).handle


class SetupTextures(SyntaxExpander):
    template = "「wrapped」"

    def __init__(self, env:Program):
        SyntaxExpander.__init__(self)
        self.wrapped:List[SyntaxExpander] = []
        for texture in env.textures.values():
            if texture.src:
                self.wrapped.append(PngTextureSetup(texture))
            elif texture.format.target == "GL_TEXTURE_2D":
                self.wrapped.append(Texture2DSetup(texture))
                if texture.clear:
                    self.wrapped.append(ClearTexture(texture))
            elif texture.format.target == "GL_TEXTURE_3D":
                self.wrapped.append(Texture3DSetup(texture))


class SwitchTextureHandles(SyntaxExpander):
    template = """
{
	GLuint Tmp = TextureHandles[「first:int」];
	TextureHandles[「first:int」] = TextureHandles[「second:int」];
	TextureHandles[「second:int」] = Tmp;
}
""".strip()
    def __init__(self, first:Texture, second:Texture):
        SyntaxExpander.__init__(self)
        self.first = first.handle
        self.second = second.handle
