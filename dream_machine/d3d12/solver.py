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


from ..handy import *
from ..syntax.grammar import *
from ..expanders import *
from .program import *


def solve_renderers(env:Program) -> Tuple[List[SyntaxExpander], Union[SyntaxExpander, str]]:
    """
    """
    return tuple(), ""


def solve(env:Program):
    """
    Solve the program!
    """

    # expanders for various things in the global scope
    globals:List[SyntaxExpander] = []

    # expanders for generated code which is called after GL is initialized before rendering starts
    setup:List[SyntaxExpander] = []

    # expanders for the window resized event
    reallocate:List[SyntaxExpander] = []

    # expanders defining the available renderers
    renderers, switch = solve_renderers(env)

    # emit the generated program
    program = GeneratedMain()
    program.window_title = "Hello World!"
    program.window_width = 512
    program.window_height = 512
    program.globals = globals
    program.initial_setup_hook = setup
    program.resize_hook = reallocate
    program.renderers = renderers
    program.draw_frame_hook = switch

    dependencies:List[str] = ["d3d12_util"]
    if len([t for t in env.textures.values() if t.src]):
        dependencies.append("images")
    header = GeneratedHeader(dependencies)

    return program, header, dependencies
