
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
from .drawspatch import *
from .window import *
from .js_expressions import *


def solve(env:Program) -> SyntaxExpander:
    """
    Solve the webpage!
    """

    # structs
    solved_structs:Dict[str,Any] = {}

    # expanders for shaders
    build_shaders:List[SyntaxExpander] = []

    # expanders for struct definitions
    structs:List[SyntaxExpander] = []

    # expanders for various things in the global scope
    globals:List[SyntaxExpander] = []

    if env.samplers:
        pass

    if env.textures:
        pass

    if env.pipelines:
        pass

    if env.buffers:
        pass

    # expanders for buffer uploaders
    uploaders:List[SyntaxExpander] = []
    if env.buffers:
        pass

    # user-defined variables
    user_vars:List[SyntaxExpander] = [ExternUserVar(v) for v in env.user_vars.values()]

    # expanders for generated code which is called after GL is initialized before rendering starts
    setup:List[SyntaxExpander] = \
    [
        DefaultVAO(),
    ]
    setup += build_shaders

    if env.samplers:
        pass

    if env.textures:
        pass

    if env.pipelines:
        pass

    if env.buffers:
        pass

    # expanders for the window resized event
    reallocate:List[SyntaxExpander] = []
    if env.pipelines:
        pass

    # expanders defining the available renderers
    renderers, switch = '', ''

    # emit the generated program
    program = WebGLWindow()
    program.globals = globals
    program.user_vars = user_vars
    program.uploaders = uploaders
    program.initial_setup_hook = setup
    program.resize_hook = reallocate
    program.renderers = renderers
    program.draw_frame_hook = switch
    return program
