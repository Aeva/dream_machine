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
from enum import IntEnum
from ..expanders import SyntaxExpander
from .js_expressions import solve_expression
from ..handy import CAST
from ..syntax.grammar import Texture, Format, TextureDimension, PipelineInput, Program
from ..syntax.constants import TextureType, TextureFormats
from ..syntax.constants import SamplerFilterType


SAMPLER_FILTER_MODES = {
    SamplerFilterType.POINT : "NEAREST",
    SamplerFilterType.LINEAR : "LINEAR",
}


class InternalFormats(IntEnum):
    """
    The values here are used to map to TextureFormats in dream_machine/syntax/constants.py.
    """

    RGBA32F = 2
    RGB32F = 6
    RGBA16F = 10
    RGBA = 28
    FLOAT = 41
    HALF_FLOAT = 54
    DEPTH_COMPONENT = 55


FORMAT_CHANNELS = \
{
    InternalFormats.RGBA32F : 4,
    InternalFormats.RGB32F : 3,
    InternalFormats.RGBA16F : 4,
    InternalFormats.RGBA : 4,
    InternalFormats.FLOAT : 1,
    InternalFormats.HALF_FLOAT : 1,
    InternalFormats.DEPTH_COMPONENT : 1,
}


def WebGLFormat(format:Format):
    generic:TextureFormat = format.format
    try:
        return "gl." + InternalFormats(generic).name
    except ValueError:
        format.error(f'Texture format not supported by the WebGL backend: "{generic.name}"')


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
		gl.texImage2D(gl.TEXTURE_2D, 0, 「format」, 「format」, gl.UNSIGNED_BYTE, Req);
	});
	Req.src = "「src:TextureSrc」";
}
""".strip()

    def __init__(self, texture:Texture):
        SyntaxExpander.__init__(self)
        self.name = texture.name
        self.handle = texture.handle
        self.format = WebGLFormat(texture.format)
        self.src = texture.src


class WritePixelChannel(SyntaxExpander):
    template = "		Upload[i + 「offset」] = 「channel」;"

    def __init__(self, offset, channel):
        SyntaxExpander.__init__(self)
        self.offset = offset
        self.channel = round(max(min(channel, 1.0), 0.0) * 255.0)


class Texture2DClearData(SyntaxExpander):
    template = """
	let Size = 「width」 * 「height」 * 「channels」;
	let Upload = new Uint8Array(Size);
	for (let i=0; i < Size; i += 「channels」)
	{
「writes」
	}
    """.strip()

    def __init__(self, texture:Texture):
        SyntaxExpander.__init__(self)
        assert(texture.format.target == TextureType.TEXTURE_2D)
        self.width = solve_expression(texture.width)
        self.height = solve_expression(texture.height)
        self.channels = FORMAT_CHANNELS[texture.format.format]
        self.writes = [WritePixelChannel(i, c) for (i, c) in enumerate(texture.clear.channels)]


class Texture2DSetup(SyntaxExpander):
    template = """
{
	TextureHandles[「handle:int」] = gl.createTexture();
	gl.bindTexture(gl.TEXTURE_2D, TextureHandles[「handle:int」]);
	「upload」
	gl.texImage2D(gl.TEXTURE_2D, 0, 「format:str」, 「width」, 「height」, 0, 「format:str」, gl.UNSIGNED_BYTE, Upload);
}
""".strip()

    def __init__(self, texture:Texture):
        SyntaxExpander.__init__(self)
        assert(texture.format.target == TextureType.TEXTURE_2D)
        self.name = texture.name
        self.handle = texture.handle
        self.format = WebGLFormat(texture.format)
        self.width = solve_expression(texture.width)
        self.height = solve_expression(texture.height)
        self.upload = Texture2DClearData(texture) if texture.clear else "let Upload = null;";


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
        assert(texture.format.target == TextureType.TEXTURE_3D)
        self.name = texture.name
        self.handle = texture.handle
        self.format = WebGLFormat(texture.format)
        self.width = solve_expression(texture.width)
        self.height = solve_expression(texture.height)
        self.depth = solve_expression(texture.depth)


class ResizeTexture2D(Texture2DSetup):
    template = """
{
	gl.deleteTexture(TextureHandles[「handle:int」]);
	TextureHandles[「handle:int」] = gl.createTexture();
	gl.bindTexture(gl.TEXTURE_2D, TextureHandles[「handle:int」]);
	「upload」
	gl.texImage2D(gl.TEXTURE_2D, 0, 「format:str」, 「width」, 「height」, 0, 「format:str」, gl.UNSIGNED_BYTE, Upload);
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
    if texture.format.target == TextureType.TEXTURE_2D:
        return ResizeTexture2D(texture)
    else:
        assert(texture.format.target == TextureType.TEXTURE_3D)
        return ResizeTexture3D(texture)


class BindTexture(SyntaxExpander):
    template = """
gl.activeTexture(gl.TEXTURE0 + 「texture_unit:int」);
gl.bindTexture(「target」, TextureHandles[「handle:int」]);
gl.texParameteri(「target」, gl.TEXTURE_MIN_FILTER, gl.「min_filter:str」);
gl.texParameteri(「target」, gl.TEXTURE_MAG_FILTER, gl.「mag_filter:str」);
gl.texParameteri(「target」, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
gl.texParameteri(「target」, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
""".strip()

    def __init__(self, binding:PipelineInput):
        SyntaxExpander.__init__(self)
        self.target = "gl." + binding.format.target.name
        self.texture_unit = binding.texture_index
        self.handle = CAST(Texture, binding.texture).handle
        sampler = binding.format.sampler
        self.min_filter = SAMPLER_FILTER_MODES[sampler.filters["min"].value]
        self.mag_filter = SAMPLER_FILTER_MODES[sampler.filters["mag"].value]


class SetupTextures(SyntaxExpander):
    template = "「wrapped」"

    def __init__(self, env:Program):
        SyntaxExpander.__init__(self)
        self.wrapped:List[SyntaxExpander] = []
        for texture in env.textures.values():
            if texture.src:
                if texture.format.target != TextureType.TEXTURE_2D:
                    texture.format.error(f'Textures loaded must use a TEXTURE_2D format."')
                self.wrapped.append(PngTextureSetup(texture))
            elif texture.format.target == TextureType.TEXTURE_2D:
                self.wrapped.append(Texture2DSetup(texture))
            elif texture.format.target == TextureType.TEXTURE_3D:
                self.wrapped.append(Texture3DSetup(texture))


class SwitchTextureHandles(SyntaxExpander):
    template = """
{
	let Tmp = TextureHandles[「first:int」];
	TextureHandles[「first:int」] = TextureHandles[「second:int」];
	TextureHandles[「second:int」] = Tmp;
}
""".strip()
    def __init__(self, texture:Texture):
        SyntaxExpander.__init__(self)
        self.first = texture.handle
        self.second = texture.shadow_texture.handle
