
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
from .syntax.grammar import validate
from .solver import solve
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
    solved = solve(env)
    with open("generated.cpp", "w", encoding="utf-8") as outfile:
        outfile.write(str(solved))
    build("generated.cpp", "user_code.cpp", out_path="generated.exe", debug=True)
