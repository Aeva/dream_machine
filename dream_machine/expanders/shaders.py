
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
from hashlib import md5
from ..handy import *
from .glsl_types import *
from .common import external


class ShaderHandles(SyntaxExpander):
    template = """
GLuint Shaders[「shader_count」] = { 0 };
GLuint ShaderPrograms[「program_count」] = { 0 };
std::string ShaderPaths[「shader_count」] = {\n「paths」\n};
""".strip()
    indent = ("paths",)


class CompileShader(SyntaxExpander):
    template = "Shaders[「index」] = CompileShader(ShaderPaths[「index」], 「stage」);"
    def __init__(self, index: int, shader):
        SyntaxExpander.__init__(self)
        self.index = index
        self.path = shader.path
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
        assert(stage in ["vertex", "fragment"])
        self.path = path
        self.stage = f"GL_{stage.upper()}_SHADER"
        class GlslTransform(SyntaxExpander):
            template = external(path)
        self.src = str(GlslTransform(shader_expanders))

    def save(self) -> str:
        name = f"{os.path.split(self.path)[-1]}.{md5(str(self).encode()).hexdigest()}.glsl"
        if not os.path.exists("generated_shaders"):
            os.mkdir("generated_shaders")
        path = os.path.join("generated_shaders", name)
        with open(path, "w") as generated:
            generated.write(self.src)
        return path.encode("unicode_escape").decode("utf8")

    def __str__(self):
        return str((self.path, self.stage, self.src))

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
