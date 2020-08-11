
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


from __future__ import annotations
import os
from base64 import b64encode
from hashlib import md5
from ..handy import *
from ..opengl.glsl_types import *
from ..expanders import SyntaxExpander, external
from ..syntax.abstract import Pipeline


class ShaderHandles(SyntaxExpander):
    template = """
let Shaders = new Array(「shader_count」);
let ShaderPrograms = new Array(「program_count」);
""".strip()


class CompileShader(SyntaxExpander):
    template = """
{
	let ShaderSource = atob("「encoded」");
	Shaders[「index」] = CompileShader(ShaderSource, 「stage」);
}
    """.strip()

    def __init__(self, index: int, shader):
        SyntaxExpander.__init__(self)
        self.index = index
        self.encoded = shader.encoded
        self.stage = shader.stage


class AssignTextureUnit(SyntaxExpander):
    template = """
const 「binding_name」 = gl.getUniformLocation(Handle, "「binding_name」");
if (「binding_name」 !== null) {
	gl.uniform1i(「binding_name」, 「texture_unit」);
}
""".strip()
    def __init__(self, texture_unit:int, binding_name:str):
        SyntaxExpander.__init__(self)
        self.binding_name = binding_name
        self.texture_unit = texture_unit


class LinkShaders(SyntaxExpander):
    template = """
{
	let Stages = new Array(「shaders」);
	let Handle = ShaderPrograms[「index:int」] = LinkShaders(Stages);
「post_link」
}
""".strip()
    indent = ("post_link",)

    def __init__(self, program:ShaderProgram, index: int, shaders:List[int]):
        SyntaxExpander.__init__(self)
        self.index = index
        self.shaders = ", ".join([f"Shaders[{shader}]" for shader in shaders])
        post_link:List[Union[str, SyntaxExpander]] = []
        if program.textures or program.uniforms:
            post_link += ["gl.useProgram(Handle);"]
        if program.textures:
            post_link += [AssignTextureUnit(u, t) for (u, t) in enumerate(program.textures)]
        self.post_link = post_link


class ChangeProgram(SyntaxExpander):
    template = """
{
	let Handle = ShaderPrograms[「index」];
	gl.useProgram(Handle);
	let AttrCount = gl.getProgramParameter(Handle, gl.ACTIVE_ATTRIBUTES);
	for (let a = 0; a < AttrCount; ++a) {
		let Attr = gl.getActiveAttrib(Handle, a);
		let Index = gl.getAttribLocation(Handle, Attr.name);
		gl.enableVertexAttribArray(Index);
		gl.vertexAttribPointer(Index, 3, gl.FLOAT, false, 0, 0);
	}
}
""".strip()


class ShaderStage:
    """
    Immutable data corresponding roughly to the parameters for the OpenGL API
    calls "glCreateShader" and "glShaderSource".
    """
    def __init__(self, stage: str, path: str, shader_expanders: List[SyntaxExpander], source: Optional[str] = None) -> None:
        assert(stage in ["vertex", "fragment"])
        self.path = path
        self.stage = f"gl.{stage.upper()}_SHADER"
        if source is None:
            class GlslTransform(SyntaxExpander):
                template = external(path)
            source = str(GlslTransform(shader_expanders))
        self.encoded = b64encode(source.encode()).decode().strip()

    def __str__(self):
        return str((self.stage, self.encoded))

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)

    def __lt__(self, other):
        return str(self) < str(other)


class ShaderProgram:
    """
    This contains a set of ShaderStage objects and a handy name.  The provided
    name is used to fill out debug events, and to identify linker info log
    entries.

    The provided shader stages can be whatever, but there should only be one
    shader per each shader stage type.  Additionally, the stages should form
    a valid pipeline.
    """
    def __init__(self, pipeline:Pipeline, shaders: List[ShaderStage]) -> None:
        self.name = pipeline.name
        self.textures = [t.binding_name for t in pipeline.textures]
        self.uniforms = pipeline.uniforms
        self.shaders = dedupe(shaders)
        self.stages = tuple(sorted([shader.stage for shader in self.shaders]))
