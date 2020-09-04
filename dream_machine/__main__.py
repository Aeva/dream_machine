
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
from .gndn import build as gndn_backend
from .opengl import build as opengl_backend
from .webgl import build as webgl_backend


CPP_BACKENDS = \
{
    BackendAPI.GNDN : gndn_backend,
    BackendAPI.OpenGL : opengl_backend,
}


def run_cpp_backend(env):
    backend = CPP_BACKENDS[env.backend.api]
    backend.validate(env)
    program, header, *etc = backend.solve(env)
    assert(program is not None)
    with open("generated.cpp", "w", encoding="utf-8") as outfile:
        outfile.write(str(program))
    with open("generated.h", "w", encoding="utf-8") as outfile:
        outfile.write(str(header))
    user_sources = ["generated.cpp", "user_code.cpp"]
    backend.build(user_sources, *etc, out_path="generated.exe", debug=True)


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

    elif env.backend.api in CPP_BACKENDS:
        run_cpp_backend(env)

    elif env.backend.api == BackendAPI.WebGL:
        webgl_backend.validate(env)
        solved = webgl_backend.solve(env)
        assert(solved is not None)
        with open("generated.js", "w", encoding="utf-8") as outfile:
            outfile.write(str(solved))
