
import math
from typing import *
from functools import reduce
from .tokens import *
from .parser import Parser
parser:Parser


ErrorCallback = Callable[..., None]
FoldedExpression = Union[int, float, str]


class ArithmeticError(Exception):
    pass


def is_even(n:Union[int, float]) -> bool:
    return (n % 2) == 0


class UnfoldedExpression:
    """
    Represents a (potentially foldable) unfolded arithmetic expression, which
    may contain other unfolded arithmetic expressions.
    """
    def __init__(self, token, error:ErrorCallback, cmd:str, args):
        self._token = token
        self._error = error
        self.cmd = cmd
        self.args = args
        self.rewrite()
        self.pivot()

    def __repr__(self):
        return f'<UnfoldedExpression ({self.cmd} {" ".join(map(repr, self.args))})>'

    def error(self, hint:str):
        self._error(hint, self._token, ArithmeticError)

    def route(self):
        try:
            fn = getattr(self, f'op_{self.cmd}')
        except AttributeError:
            self.error(f'Unknown arithmetic operation: "{self.cmd}"')
        return fn()

    def fold(self):
        folded = self.route()
        if not self.unfoldable:
            assert(folded is not None)
            return folded
        else:
            prepend = [] if folded is None else [folded]
            return UnfoldedExpression(self._token, self._error, self.cmd, prepend + self.unfoldable)

    def rewrite(self):
        if self.cmd == "mad":
            if len(self.args) < 3 or is_even(len(self.args)):
                self.error(f'Arithmetic operation "{self.cmd}" expects an odd number of at least 3 parameters, got {len(self.args)}.')
            evens = self.args[::2]
            odds = self.args[1::2]
            last = evens.pop()
            self.args = [UnfoldedExpression(self._token, self._error, "mul", pair).fold() for pair in zip(evens, odds)] + [last]
            self.cmd = "add"

    def pivot(self):
        pivot = 0
        for arg in self.args:
            if type(arg) in (int, float):
                pivot += 1
            else:
                break
        self.foldable = self.args[:pivot]
        self.unfoldable = self.args[pivot:]

    def variadic(self, min_args=2):
        if len(self.args) < min_args:
            self.error(f'Arithmetic operation "{self.cmd}" expects at least {min_args} parameters, got {len(self.args)}.')
        if len(self.foldable) < min_args:
            self.unfoldable = self.foldable + self.unfoldable
            self.foldable = []

    def fixed(self, expected):
        if len(self.args) < expected:
            self.error(f'Arithmetic operation "{self.cmd}" expects exactly {expected} parameters, got {len(self.args)}.')
        if self.unfoldable:
            # all or nothing
            self.unfoldable = self.foldable + self.unfoldable
            self.foldable = []

    def op_add(self):
        self.variadic()
        if self.foldable:
            return sum(self.foldable)
        return None

    def op_sub(self):
        self.variadic()
        if self.foldable:
            return self.foldable[0] - sum(self.foldable[1:])
        return None

    def op_mul(self):
        self.variadic()
        if self.foldable:
            return reduce(lambda x, y: x * y, self.foldable)
        return None

    def op_div(self):
        self.variadic()
        if self.foldable:
            return reduce(lambda x, y: x / y, self.foldable)
        return None

    def op_min(self):
        self.variadic()
        if self.foldable:
            return min(self.foldable)
        return None

    def op_max(self):
        self.variadic()
        if self.foldable:
            return max(self.foldable)
        return None

    def op_sin(self):
        self.fixed(1)
        if self.foldable:
            return math.sin(*self.foldable)
        return None

    def op_cos(self):
        self.fixed(1)
        if self.foldable:
            return math.cos(*self.foldable)
        return None

    def op_tan(self):
        self.fixed(1)
        if self.foldable:
            return math.tan(*self.foldable)
        return None


def fold(token:Token, error:ErrorCallback) -> Union[FoldedExpression, UnfoldedExpression]:
    """
    Recursively attempts to fold an arithmetic expression represented by a tree of tokens.
    Returns either a numeric value, a string, or an UnfoldedExpression instance.
    """

    if type(token) is TokenNumber:
        return cast(TokenNumber, token).value

    elif type(token) is TokenWord:
        name = str(token)
        if name == "pi":
            return math.pi
        else:
            return name

    elif type(token) is TokenList:
        tokens = cast(TokenList, token)
        if tokens.is_nil():
            error("TokenList is empty.", tokens)

        cmd = cast(Token, tokens[0])
        if type(cmd) is not TokenWord:
            error("Expected TokenWord", cmd)
        args = [fold(t, error) for t in cast(Tuple[Token], tokens[1:])]
        expr = UnfoldedExpression(token, error, str(cmd), args)
        return expr.fold()

    else:
        error("Expected TokenNumber, TokenWord, or TokenList.", token)
        return ""
