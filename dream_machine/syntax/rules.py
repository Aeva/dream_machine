
import itertools
from .abstract import *


class Rule:
    """
    Base class for grammar validation rules.
    """
    def constructors(self) -> List[type]:
        return []

    def validate(self, token:Token, error:ErrorCallback) -> Optional[Syntax]:
        raise NotImplementedError
        return False

    def match(self, token:Token) -> bool:
        raise NotImplementedError
        return False


class AtomRule(Rule):
    """
    Matches a token when the token is not a TokenList or TokenComment.
    """
    def __init__(self, hint:str, atom:type):
        self.hint = hint
        self.atom = atom

    def validate(self, token:Token, error:ErrorCallback) -> Optional[Syntax]:
        if not type(token) == self.atom:
            error(f"Expected {self.hint} to be a {self.atom}, got {type(token).__name__}", token)
        return None

    def match(self, token:Token) -> bool:
        # we don't want to be too strict in the pattern match,
        # so we just ensure that we have an atom here.
        return type(token) is not TokenList

    def __repr__(self):
        return f'<{type(self).__name__} "{self.hint}">'


class WordRule(AtomRule):
    """
    Matches a single TokenWord.
    """
    def __init__(self, hint:str):
        AtomRule.__init__(self, hint, TokenWord)


class StringRule(AtomRule):
    """
    Matches a single TokenString.
    """
    def __init__(self, hint:str):
        AtomRule.__init__(self, hint, TokenString)


class NumberRule(AtomRule):
    """
    Matches a single TokenNumber.
    """
    def __init__(self, hint:str):
        AtomRule.__init__(self, hint, TokenNumber)


class Exactly(WordRule):
    """
    Matches a single TokenWord where the token's vaule is exactly equal to the
    specified value.
    """
    def __init__(self, name:str):
        WordRule.__init__(self, name)

    def validate(self, token:Token, error:ErrorCallback) -> Optional[Syntax]:
        WordRule.validate(self, token, error)
        if str(token) != self.hint:
            error(f"Expected {self.hint}, got {str(token)}...?", token)
        return None

    def match(self, token:Token) -> bool:
        if type(token) == TokenWord:
            return str(token) == self.hint
        else:
            return False

    def __repr__(self):
        return f'<Exactly "{self.hint}">'


class ArithmeticRule(Rule):
    """
    This will attempt to match a valid arithmetic expresison.
    """

    def __init__(self, hint:str):
        self.hint = hint

    def constructors(self) -> List[type]:
        return [ArithmeticExpression]

    def validate(self, token:Token, error:ErrorCallback) -> Optional[Syntax]:
        expr:Union[FoldedExpression, UnfoldedExpression] = fold(token, error)
        return ArithmeticExpression(expr, token, [], [])

    def match(self, token:Token) -> bool:
        # expressions can look like lots of things
        return True


class ListRule(Rule):
    """
    Matches a sequence of rules within a TokenList.  When successfully validated,
    this will produce syntax objects.  This is typically used within a MatchRule,
    but may also be used as a splat.  Each instance must specify what Syntax type
    will be created, in addition to the rules list etc.
    """
    def __init__(self, construct:Type[Syntax], *rules:Rule, SPLAT:Optional[Rule] = None):
        self.construct = construct
        self.rules = rules
        self.splat = SPLAT

    def constructors(self) -> List[type]:
        return [self.construct]

    def validate(self, token:Token, error:ErrorCallback) -> Optional[Syntax]:
        if type(token) is not TokenList:
            error(f"Expected TokenList, got {type(token).__name__}", token)
        token_list = cast(TokenList, token).without_comments()
        if self.splat:
            if len(token_list) <= len(self.rules):
                error(f"Expected more than {len(self.rules)} list items, got {len(token_list)}", token_list)
        elif len(token_list) != len(self.rules):
            error(f"Expected exactly {len(self.rules)} list items, got {len(token_list)}", token_list)
        children:List[Syntax] = []
        child_types = []
        for rule, token in zip(self.rules, token_list):
            syntax = rule.validate(token, error)
            if syntax:
                children.append(syntax)
                child_types += rule.constructors()
        if self.splat:
            remainder = cast(Tuple[Token], token_list[len(self.rules):])
            child_types += self.splat.constructors()
            for token in remainder:
                syntax = self.splat.validate(token, error)
                if syntax is not None:
                    children.append(cast(Syntax, syntax))
        return self.construct(token_list, children, child_types)

    def match(self, token:Token) -> bool:
        token_list = CAST(TokenList, token)
        for rule, token in zip(self.rules, token_list):
            if not rule.match(token):
                return False
        return True

    def __repr__(self):
        return "<ListRule>"


class MatchRule(Rule):
    """
    This will attempt to match a TokenList to one of the associated ListRule
    parameters.
    """
    def __init__(self, *rules:ListRule):
        self.rules = rules

    def constructors(self) -> List[type]:
        return [rule.construct for rule in self.rules]

    def validate(self, token:Token, error:ErrorCallback) -> Optional[Syntax]:
        token_list = CAST(TokenList, token).without_comments()
        if token_list.is_nil():
            error("Expected non-empty TokenList", token_list)
        for rule in self.rules:
            if rule.match(token_list):
                return rule.validate(token_list, error)
        error("Unkown expression", token_list)
        return None

    def __repr__(self):
        return "<MatchRule>"
