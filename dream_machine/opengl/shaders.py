
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
from .glsl_types import *
from ..expanders import external


class ShaderHandles(SyntaxExpander):
    template = """
GLuint Shaders[「shader_count」] = { 0 };
GLuint ShaderPrograms[「program_count」] = { 0 };
""".strip()


class CompileShader(SyntaxExpander):
    template = """
{
	std::string ShaderSource = DecodeBase64(\"「encoded」\");
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
	GLuint Stages[「shader_count」] = { 「shaders」 };
	ShaderPrograms[「index」] = LinkShaders(\"「name」\", &Stages[0], 「shader_count」);
}
""".strip()
    def __init__(self, name: str, index: int, shaders:List[int]):
        SyntaxExpander.__init__(self)
        self.name = name
        self.index = str(index)
        self.shader_count = str(len(shaders))
        self.shaders = ", ".join([f"Shaders[{shader}]" for shader in shaders])


class ChangeProgram(SyntaxExpander):
    template = "glUseProgram(ShaderPrograms[「index」]);"


class ShaderStage:
    """
    Immutable data corresponding roughly to the parameters for the OpenGL API
    calls "glCreateShader" and "glShaderSource".
    """
    def __init__(self, stage: str, path: str, shader_expanders: List[SyntaxExpander]) -> None:
        assert(stage in ["vertex", "fragment", "compute"])
        self.path = path
        self.stage = f"GL_{stage.upper()}_SHADER"
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
