
import math
from typing import *
from .tokens import *
from .parser import Parser
parser:Parser


Number = Union[int, float]
FoldedExpression = Union[Number, str]
BinaryOperator = Callable[[Any, Number, Number], Number]
ErrorCallback = Callable[..., None]


def binary_op(fn:BinaryOperator) -> BinaryOperator:
    setattr(fn, "tag", "binary")
    return fn


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

    def __repr__(self):
        return f'<UnfoldedExpression ({self.cmd} {" ".join(map(repr, self.args))})>'

    def rewrite(self):
        if self.cmd == "mad":
            # Rewrites mads in the form of (add (mul a b) (mul c d) e) to make
            # constant folding easier and better.
            if len(self.args) < 3 or is_even(len(self.args)):
                self.error(f'Arithmetic operation "{self.cmd}" expects an odd number of at least 3 parameters, got {len(self.args)}.')
            evens = self.args[::2]
            odds = self.args[1::2]
            last = evens.pop()
            self.args = [UnfoldedExpression(self._token, self._error, "mul", pair).fold() for pair in zip(evens, odds)] + [last]
            self.cmd = "add"

        if self.cmd == "div" and len(self.args) > 2:
            # Rewrites divs in the form of (div num num (mul pivot etc etc etc))
            # so everything can be folded instead of just the beginning.
            pivot = 0
            for arg in self.args:
                if type(arg) in (int, float):
                    pivot += 1
                else:
                    break
            pivot = max(pivot, 1)
            keep = self.args[:pivot]
            rewrite = self.args[pivot:]
            if rewrite:
                self.args = keep + [UnfoldedExpression(self._token, self._error, "mul", rewrite).fold()]

    def fold_binary_op(self, fn):
        if len(self.args) < 2:
            self.error(f'Arithmetic operation "{self.cmd}" expects at least {min_args} parameters, got {len(self.args)}.')
        new_args = []
        acc = None
        for arg in self.args:
            if type(arg) in (int, float):
                if acc is None:
                    acc = arg
                    continue
                acc = fn(acc, arg)
                continue
            else:
                if acc is not None:
                    new_args.append(acc)
                    acc = None
                new_args.append(arg)
                continue
        if new_args:
            if acc is not None:
                new_args.append(acc)
            self.args = new_args
            return self
        else:
            assert(acc is not None)
            return acc

    def fold_fixed_op(self, fn):
        if [i for i in self.args if not type(i) in (int, float)]:
            return self
        else:
            return fn()

    def fold(self):
        try:
            fn = getattr(self, f'op_{self.cmd}')
        except AttributeError:
            self.error(f'Unknown arithmetic operation: "{self.cmd}"')
        if getattr(fn, "tag", "") == "binary":
            return self.fold_binary_op(fn)
        else:
            return self.fold_fixed_op(fn)

    def fixed(self, expected):
        if len(self.args) < expected:
            self.error(f'Arithmetic operation "{self.cmd}" expects exactly {expected} parameters, got {len(self.args)}.')

    @binary_op
    def op_add(self, a:Number, b:Number) -> Number:
        return a + b

    @binary_op
    def op_sub(self, a:Number, b:Number) -> Number:
        return a - b

    @binary_op
    def op_mul(self, a:Number, b:Number) -> Number:
        return a * b

    @binary_op
    def op_div(self, a:Number, b:Number) -> Number:
        return a / b

    @binary_op
    def op_min(self, a:Number, b:Number) -> Number:
        return min(a, b)

    @binary_op
    def op_max(self, a:Number, b:Number) -> Number:
        return max(a, b)

    def op_sin(self):
        self.fixed(1)
        return math.sin(*self.args)

    def op_cos(self):
        self.fixed(1)
        return math.cos(*self.args)

    def op_tan(self):
        self.fixed(1)
        return math.tan(*self.args)


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
