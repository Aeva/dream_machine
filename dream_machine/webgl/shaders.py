
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


import os
from base64 import b64encode
from hashlib import md5
from ..handy import *
from ..opengl.glsl_types import *
from ..expanders import SyntaxExpander, external


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


class LinkShaders(SyntaxExpander):
    template = """
{
	let Stages = new Array(「shaders」);
	ShaderPrograms[「index」] = LinkShaders(Stages);
}
""".strip()
    def __init__(self, name: str, index: int, shaders:List[int]):
        SyntaxExpander.__init__(self)
        self.name = name
        self.index = str(index)
        self.shader_count = str(len(shaders))
        self.shaders = ", ".join([f"Shaders[{shader}]" for shader in shaders])


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
    def __init__(self, name: str, shaders: List[ShaderStage]) -> None:
        self.name = name
        self.shaders = dedupe(shaders)
        self.stages = tuple(sorted([shader.stage for shader in self.shaders]))
