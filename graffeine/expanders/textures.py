
from typing import *
from .common import SyntaxExpander
from ..handy import CAST
from ..syntax.grammar import Texture, TextureWidth, TextureHeight, TextureDepth, RendererDrawBind, Program


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
	glTextureStorage2D(TextureHandles[「handle:int」], 1, 「format:str」, 「width:int」, 「height:int」);
	glObjectLabel(GL_TEXTURE, TextureHandles[「handle:int」], -1, \"「name:str」\");
}
""".strip()

    def __init__(self, texture:Texture):
        SyntaxExpander.__init__(self)
        self.name = texture.name
        self.handle = texture.handle
        self.format = texture.format.format
        self.width = cast(TextureWidth, texture.width).value
        self.height = cast(TextureHeight, texture.height).value


class Texture3DSetup(SyntaxExpander):
    template = """
{
	// texture "「name:str」"
	glCreateTextures(GL_TEXTURE_3D, 1, &TextureHandles[「handle:int」]);
	glTextureStorage3D(TextureHandles[「handle:int」], 1, 「format:str」, 「width:int」, 「height:int」, 「depth:int」);
	glObjectLabel(GL_TEXTURE, TextureHandles[「handle:int」], -1, \"「name:str」\");
}
""".strip()

    def __init__(self, texture:Texture):
        SyntaxExpander.__init__(self)
        self.name = texture.name
        self.handle = texture.handle
        self.format = texture.format.format
        self.width = cast(TextureWidth, texture.width).value
        self.height = cast(TextureHeight, texture.height).value
        self.depth = cast(TextureDepth, texture.depth).value


class BindTexture(SyntaxExpander):
    template = "glBindTextureUnit(「texture_unit」, TextureHandles[「handle」]);"

    def __init__(self, binding:RendererDrawBind):
        SyntaxExpander.__init__(self)
        self.texture_unit = binding.interface.texture_unit
        self.handle = binding.texture.handle


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
            elif texture.format == "GL_TEXTURE_2D":
                self.wrapped.append(Texture2DSetup(texture))
            elif texture.format == "GL_TEXTURE_3D":
                self.wrapped.append(Texture3DSetup(texture))
