
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
from .cpp_expressions import solve_expression
from ..handy import CAST
from ..syntax.grammar import Texture, TextureDimension, PipelineInput, Program


class TextureHandles(SyntaxExpander):
    template = "GLuint TextureHandles[「count:int」] = { 0 };"


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
        self.format = texture.format.format
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
        self.format = texture.format.format
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
        self.format = texture.format.format
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
    template = """
{
「wrapped」
}
""".strip()
    indent = ("wrapped",)

    def __init__(self, env:Program):
        SyntaxExpander.__init__(self)
        self.wrapped:List[SyntaxExpander] = []
        for texture in env.textures.values():
            if texture.src:
                self.wrapped.append(PngTextureSetup(texture))
            elif texture.format.target == "GL_TEXTURE_2D":
                self.wrapped.append(Texture2DSetup(texture))
            elif texture.format.target == "GL_TEXTURE_3D":
                self.wrapped.append(Texture3DSetup(texture))
