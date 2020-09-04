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


def solve(env:Program):
    """
    Solve the program!
    """

    # emit the generated program
    program = GeneratedMain()
    program.window_title = "Goes Nowhere, Does Nothing"
    program.window_width = 512
    program.window_height = 512

    dependencies:List[str] = []
    if len([t for t in env.textures.values() if t.src]):
        dependencies.append("images")
    header = GeneratedHeader(dependencies)

    return program, header, dependencies
