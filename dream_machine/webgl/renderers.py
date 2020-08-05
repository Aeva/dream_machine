
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


class RendererCall(SyntaxExpander):
    template = """
"「name」" : function(FrameIndex, CurrentTime, DeltaTime) {
「calls」
},
""".strip()
    indent = ("calls",)


class RendererCase(SyntaxExpander):
    template = """
case 「index」:
	Renderer["「name」"](FrameIndex, CurrentTime, DeltaTime);
	break;
""".strip()


class RendererSwitch(SyntaxExpander):
    template = """
switch (CurrentRenderer) {
「cases」
default:
	throw new Error("Invalid renderer index: " + CurrentRenderer);
}
""".strip()
