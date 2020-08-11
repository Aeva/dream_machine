
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


from ..expanders import SyntaxExpander, external


class WebGLWindowClosure(SyntaxExpander):
    template = """
"use strict";

let UserVars = {
「user_vars」
}
let CurrentRenderer = 0;
let gl = null;

(function() {
「wrapped」
})();
    """.strip()
    indent = ("user_vars", "wrapped")


class WebGLWindow(SyntaxExpander):
    template = external("webgl/main.js")
    indent = ("initial_setup_hook", "resize_hook", "draw_frame_hook", "renderers", "uploaders")
