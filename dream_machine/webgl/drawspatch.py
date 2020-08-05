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


from ..expanders import SyntaxExpander


class ColorClear(SyntaxExpander):
    template="gl.clearColor(「color」);\ngl.clear(gl.COLOR_BUFFER_BIT);"
    def __init__(self, red: float, green: float, blue: float, alpha: float=1.0):
        SyntaxExpander.__init__(self)
        self.color = ", ".join(map(str, [red, green, blue, alpha]))


class DepthClear(SyntaxExpander):
    template = "gl.clearDepth(「depth:int」);\ngl.clear(gl.DEPTH_BUFFER_BIT);"


class Capability(SyntaxExpander):
    template = "gl.「state_prefix」able(gl.「capability」);"
    def __init__(self, capability: str, state: bool):
        SyntaxExpander.__init__(self)
        self.state_prefix = "en" if state else "dis"
        self.capability = capability


class DefaultVBO(SyntaxExpander):
    template = """
{
	const SplatData = new Float32Array([
		 1.0,  1.0, 0.0,
		-1.0,  1.0, 0.0,
		-1.0, -1.0, 0.0,
		-1.0, -1.0, 0.0,
		 1.0, -1.0, 0.0,
		 1.0,  1.0, 0.0]);
	let vbo = gl.createBuffer();
	gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
	gl.bufferData(gl.ARRAY_BUFFER, SplatData, gl.STATIC_DRAW);
}
""".strip()


class Draw(SyntaxExpander):
    template = "gl.drawArrays(gl.TRIANGLES, 0, 「vertices」);"


class InstancedDraw(SyntaxExpander):
    template = "gl.drawArraysInstanced(gl.TRIANGLES, 0, 「vertices」, 「instances」);"


class Drawspatch(SyntaxExpander):
    template = """
{
「setup」
「draw」
}
""".strip()
    indent=("setup", "draw",)
