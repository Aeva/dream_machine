
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
from .js_expressions import solve_expression
from ..handy import CAST
from ..syntax.grammar import Texture, TextureDimension, PipelineInput, Program


class TextureHandles(SyntaxExpander):
    template = "let TextureHandles = new Array(「count:int」);"


class PngTextureSetup(SyntaxExpander):
    template = """
{
	let Handle = TextureHandles[「handle:int」] = PlaceHolderTexture();
	gl.bindTexture(gl.TEXTURE_2D, Handle, 0);
	let Req = new Image();
	Req.addEventListener("load", function() {
		gl.deleteTexture(TextureHandles[「handle:int」]);
		let Handle = TextureHandles[「handle:int」] = gl.createTexture();
		gl.bindTexture(gl.TEXTURE_2D, Handle);
		gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
		gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, Req);
	});
	Req.src = "「src:TextureSrc」";
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
	TextureHandles[「handle:int」] = gl.createTexture();
	gl.bindTexture(gl.TEXTURE_2D, TextureHandles[「handle:int」]);
	gl.texImage2D(gl.TEXTURE_2D, 0, 「format:str」, 「width」, 「height」, 0, 「format:str」, gl.UNSIGNED_BYTE, null);
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
	TextureHandles[「handle:int」] = gl.createTexture();
	gl.bindTexture(gl.TEXTURE_3D, TextureHandles[「handle:int」]);
	gl.texImage3D(gl.TEXTURE_3D, 0, 「format:str」, 「width」, 「height」, 「depth」, 0, 「format:str」, gl.UNSIGNED_BYTE, null);
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
	gl.deleteTexture(TextureHandles[「handle:int」]);
	TextureHandles[「handle:int」] = gl.createTexture();
	gl.bindTexture(gl.TEXTURE_2D, TextureHandles[「handle:int」]);
	gl.texImage2D(gl.TEXTURE_2D, 0, 「format:str」, 「width」, 「height」, 0, 「format:str」, gl.UNSIGNED_BYTE, null);
}
""".strip()


class ResizeTexture3D(Texture3DSetup):
    template = """
{
	gl.deleteTexture(TextureHandles[「handle:int」]);
	TextureHandles[「handle:int」] = gl.createTexture();
	gl.bindTexture(gl.TEXTURE_3D, TextureHandles[「handle:int」]);
	gl.texImage3D(gl.TEXTURE_3D, 0, 「format:str」, 「width」, 「height」, 「depth」, 0, 「format:str」, gl.UNSIGNED_BYTE, null);
}
""".strip()


def ResizeTexture(texture:Texture) -> SyntaxExpander:
    if texture.format.target == "GL_TEXTURE_2D":
        return ResizeTexture2D(texture)
    else:
        assert(texture.format.target == "GL_TEXTURE_3D")
        return ResizeTexture3D(texture)


class BindTexture(SyntaxExpander):
    template = """
gl.activeTexture(gl.TEXTURE0 + 「texture_unit:int」);
gl.bindTexture(「target」, TextureHandles[「handle:int」]);
gl.texParameteri(「target」, gl.TEXTURE_MIN_FILTER, 「min_filter:str」);
gl.texParameteri(「target」, gl.TEXTURE_MAG_FILTER, 「mag_filter:str」);
gl.texParameteri(「target」, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
gl.texParameteri(「target」, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
""".strip()

    def __init__(self, binding:PipelineInput):
        SyntaxExpander.__init__(self)
        self.target = "gl." + binding.format.target[3:]
        self.texture_unit = binding.texture_index
        self.handle = CAST(Texture, binding.texture).handle
        sampler = binding.format.sampler
        self.min_filter = "gl." + sampler.filters["min"].value[3:]
        self.mag_filter = "gl." + sampler.filters["mag"].value[3:]


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
            elif texture.format.target == "GL_TEXTURE_3D":
                self.wrapped.append(Texture3DSetup(texture))
