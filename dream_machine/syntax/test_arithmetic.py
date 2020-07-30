
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


import math
from ..handy import *
from .tokens import *
from .parser import Parser
from .grammar import GrammarError
from .arithmetic import fold, UnfoldedExpression


def fold_src(source:str):
    p = Parser()
    p.reset(source)
    tokens = p.parse()
    assert(len(tokens) == 1)
    def error(hint:str, token:Token, ErrorType=GrammarError):
        message = p.message(hint, *token.pos(), *token.pos())
        raise ErrorType(message)
    return fold(tokens[0], error)


def test_fold():
    src = "(add 1 2 (sub 1 2 3) 4)"
    fnord = fold_src(src)
    equiv = (1 + 2 + (1 - 2 - 3) + 4)
    assert(fnord == equiv)


def test_add():
    src = "(add 1 2 3 4 5)"
    fnord = fold_src(src)
    equiv = (1 + 2 + 3 + 4 + 5)


def test_sub():
    src = "(sub 1 2 3 4 5)"
    fnord = fold_src(src)
    equiv = (1 - 2 - 3 - 4 - 5)


def test_mul():
    src = "(mul 1 2 3 4 5)"
    fnord = fold_src(src)
    equiv = (1 * 2 * 3 * 4 * 5)


def test_div():
    src = "(div 1 2 3 4 5)"
    fnord = fold_src(src)
    equiv = (1 / 2 / 3 / 4 / 5)


def test_mad():
    src = "(mad 1 2 3 4 5 6 7 8 9)"
    fnord = fold_src(src)
    equiv = (1 * 2) + (3 * 4) + (5 * 6) + (7 * 8) + 9
    assert(fnord == equiv)


def test_min():
    src = "(min 1 2 3 4 5)"
    fnord = fold_src(src)
    equiv = min(1, 2, 3, 4, 5)
    assert(fnord == equiv)


def test_max():
    src = "(max 1 2 3 4 5)"
    fnord = fold_src(src)
    equiv = max(1, 2, 3, 4, 5)
    assert(fnord == equiv)


def test_sin():
    src = "(sin pi)"
    fnord = fold_src(src)
    equiv = math.sin(math.pi)
    assert(fnord == equiv)


def test_cos():
    src = "(cos pi)"
    fnord = fold_src(src)
    equiv = math.cos(math.pi)
    assert(fnord == equiv)


def test_tan():
    src = "(tan pi)"
    fnord = fold_src(src)
    equiv = math.tan(math.pi)
    assert(fnord == equiv)


def test_unfolded_1():
    src = "(mul (div 1 2) some_var)"
    fnord = fold_src(src)
    assert(type(fnord) is UnfoldedExpression)
    assert(str(fnord.cmd) == "mul")
    assert(len(fnord.args) == 2)
    assert(fnord.args[0] == 0.5)
    assert(fnord.args[1] == "some_var")


def test_unfolded_2():
    src = "(mul some_var (div 1 2))"
    fnord = fold_src(src)
    assert(type(fnord) is UnfoldedExpression)
    assert(str(fnord.cmd) == "mul")
    assert(len(fnord.args) == 2)
    assert(fnord.args[0] == "some_var")
    assert(fnord.args[1] == 0.5)


def test_partial_fold_1():
    src = "(mul 2 3 4 5 6 some_var)"
    fnord = fold_src(src)
    assert(type(fnord) is UnfoldedExpression)
    assert(str(fnord.cmd) == "mul")
    assert(len(fnord.args) == 2)
    assert(fnord.args[0] == 2 * 3 * 4 * 5 * 6)
    assert(fnord.args[1] == "some_var")


def test_partial_fold_2():
    src = "(mul 2 3 some_var 4 5 6)"
    fnord = fold_src(src)
    assert(type(fnord) is UnfoldedExpression)
    assert(str(fnord.cmd) == "mul")
    assert(len(fnord.args) == 3)
    assert(fnord.args[0] == 2 * 3)
    assert(fnord.args[1] == "some_var")
    assert(fnord.args[2] == 4 * 5 * 6)


def test_partial_fold_3():
    src = "(mad 2 3 fnord 4 5 6 7)"
    fnord = fold_src(src)
    assert(type(fnord) is UnfoldedExpression)
    assert(type(fnord) is UnfoldedExpression)
    assert(str(fnord.cmd) == "add")
    assert(len(fnord.args) == 3)
    assert(fnord.args[0] == 2 * 3)
    assert(type(fnord.args[1]) is UnfoldedExpression)
    assert(len(fnord.args[1].args) == 2)
    assert(fnord.args[1].args[0] == "fnord")
    assert(fnord.args[1].args[1] == 4)
    assert(fnord.args[2] == 37)


def test_partial_fold_4():
    src = "(mul 2 foo 4 bar 6)"
    fnord = fold_src(src)
    assert(type(fnord) is UnfoldedExpression)
    assert(str(fnord.cmd) == "mul")
    assert(len(fnord.args) == 5)
    assert(fnord.args[0] == 2)
    assert(fnord.args[1] == "foo")
    assert(fnord.args[2] == 4)
    assert(fnord.args[3] == "bar")
    assert(fnord.args[4] == 6)
