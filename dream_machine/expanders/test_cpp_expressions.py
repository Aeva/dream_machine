
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
from ..syntax.tokens import *
from ..syntax.parser import Parser
from ..syntax.grammar import GrammarError
from ..syntax.arithmetic import fold, UnfoldedExpression
from .cpp_expressions import *


def case(source:str):
    p = Parser()
    p.reset(source)
    tokens = p.parse()
    assert(len(tokens) == 1)
    def error(hint:str, token:Token, ErrorType=GrammarError):
        message = p.message(hint, *token.pos(), *token.pos())
        raise ErrorType(message)
    return solve_expression(fold(tokens[0], error))


def test_basic():
    src = "(div 6 4 2 fnord 5 2)"
    fnord = case(src)
    assert(str(fnord) == "(0.75 / (UserVars::fnord * 10))")
