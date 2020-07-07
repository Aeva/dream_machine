
from .common import SyntaxExpander
from ..solvers.intermediary import Texture, Texture2D
from ..handy import CAST


class TextureHandles(SyntaxExpander):
    template = "GLuint TextureHandles[「count:int」] = { 0 };"


class CreateTexture(SyntaxExpander):
    template = """
{
	// Create and allocate texture 「name:str」
	glCreateTextures(GL_TEXTURE_2D, 1, &TextureHandles[「handle:int」]);
	glTextureStorage2D(&TextureHandles[「handle:int」], 1, 「format:str」, 「width:int」, 「height:int」);
	glObjectLabel(GL_TEXTURE, &TextureHandles[「handle:int」], -1, 「name:str」);
}
""".strip()
    def __init__(self, handle:int, texture:Texture):
        SyntaxExpander.__init__(self)
        texture = CAST(Texture2D, texture)
        self.handle = handle
        self.name = texture.name
        self.format = texture.format # uh
        self.width = 128 # uhhh
        self.height = 128 # uhhhhhhhhhhhhh


class DeleteTexture(SyntaxExpander):
    template = "glDeleteTextures(1, &TextureHandles[「handle」]);"
