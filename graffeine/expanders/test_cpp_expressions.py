
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
    return expression_expander(fold(tokens[0], error))


def test_basic():
    src = "(div 6 4 2 fnord 5 2)"
    fnord = case(src)
    assert(str(fnord) == "(0.75 / (fnord * 10))")
