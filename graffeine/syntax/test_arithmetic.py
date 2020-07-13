
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
