
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


import sys
from .syntax.parser import Parser
from .syntax.grammar import validate, ValidationError
from .syntax.constants import BackendAPI
from .opengl.solver import solve as solve_for_opengl
from .opengl.validate import validate as validate_for_opengl
from .webgl.solver import solve as solve_for_webgl
from .webgl.validate import validate as validate_for_webgl
from .build import build


if __name__ == "__main__":
    try:
        src_path = sys.argv[1]
    except IndexError:
        print("Missing source file path.")
        exit(1)
    parser = Parser()
    parser.open(src_path)
    env = validate(parser)

    if not env.backend:
        raise ValidationError("No backend specified.")

    elif env.backend.api == BackendAPI.OpenGL:
        validate_for_opengl(env)
        program, header, dependencies = solve_for_opengl(env)
        assert(program is not None)
        with open("generated.cpp", "w", encoding="utf-8") as outfile:
            outfile.write(str(program))
        with open("generated.h", "w", encoding="utf-8") as outfile:
            outfile.write(str(header))
        user_sources = ["generated.cpp", "user_code.cpp"]
        build(user_sources, dependencies, "OpenGL", out_path="generated.exe", debug=True)

    elif env.backend.api == BackendAPI.WebGL:
        validate_for_webgl(env)
        solved = solve_for_webgl(env)
        assert(solved is not None)
        with open("generated.js", "w", encoding="utf-8") as outfile:
            outfile.write(str(solved))

