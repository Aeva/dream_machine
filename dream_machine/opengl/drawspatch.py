
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


from ..expanders import SyntaxExpander
from .shaders import ShaderProgram, ChangeProgram


class ColorClear(SyntaxExpander):
    template="glClearColor(「color」);\nglClear(GL_COLOR_BUFFER_BIT);"
    def __init__(self, red: float, green: float, blue: float, alpha: float=1.0):
        SyntaxExpander.__init__(self)
        self.color = ", ".join(map(str, [red, green, blue, alpha]))


class DepthClear(SyntaxExpander):
    template = "glClearDepth(「depth:int」);\nglClear(GL_DEPTH_BUFFER_BIT);"


class Capability(SyntaxExpander):
    template = "gl「state_prefix」able(「capability」);"
    def __init__(self, capability: str, state: bool):
        SyntaxExpander.__init__(self)
        self.state_prefix = "En" if state else "Dis"
        self.capability = capability


class DefaultVAO(SyntaxExpander):
    template = """
{
	GLuint vao;
	glGenVertexArrays(1, &vao);
	glBindVertexArray(vao);
}
""".strip()


class InstancedDraw(SyntaxExpander):
    template = "glDrawArraysInstanced(GL_TRIANGLES, 0, 「vertices」, 「instances」);"


class Drawspatch(SyntaxExpander):
    template = """
{
	glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, "「name」");
「setup」
「draw」
	glPopDebugGroup();
}
""".strip()
    indent=("setup", "draw",)


def splat(index:int , program:ShaderProgram) -> SyntaxExpander:
    """
    Creates a Drawspatch expander corresponding to a draw call of six verts
    which is for producing a full screen draw.
    """
    return Drawspatch(
        name = program.name,
        setup = ChangeProgram(index),
        draw = InstancedDraw(vertices=3, instances=1))
