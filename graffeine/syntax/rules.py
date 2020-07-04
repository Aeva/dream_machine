
from ..handy import *
from .tokens import *


ErrorCallback = Callable[[str, Token], None]


class Rule:
    def validate(self, token:Token, error:ErrorCallback):
        raise NotImplementedError
        return False


class AtomRule(Rule):
    def __init__(self, hint:str, atom:type):
        self.hint = hint
        self.atom = atom

    def validate(self, token:Token, error:ErrorCallback):
        if not type(token) == self.atom:
            error(f"Expected {self.hint} to be a {self.atom}, got {type(token).__name__}", token)

    def __repr__(self):
        return f'<{type(self).__name__} "{self.hint}">'


class WordRule(AtomRule):
    def __init__(self, hint:str):
        AtomRule.__init__(self, hint, TokenWord)


class StringRule(AtomRule):
    def __init__(self, hint:str):
        AtomRule.__init__(self, hint, TokenString)


class NumberRule(AtomRule):
    def __init__(self, hint:str):
        AtomRule.__init__(self, hint, TokenNumber)


class Exactly(WordRule):
    def __init__(self, name:str):
        WordRule.__init__(self, name)

    def validate(self, token:Token, error:ErrorCallback):
        WordRule.validate(self, token, error)
        if str(token) != self.hint:
            error(f"Expected {self.hint}, got {str(token)}...?", token)

    def match(self, token:Token) -> bool:
        if type(token) == TokenWord:
            return str(token) == self.hint
        else:
            return False

    def __repr__(self):
        return f'<Exactly "{self.name}">'


class ListRule(Rule):
    def __init__(self, *rules:Rule, SPLAT:Optional[Rule] = None):
        self.rules = rules
        self.splat = SPLAT

    def validate(self, token:Token, error:ErrorCallback):
        if type(token) is not TokenList:
            error(f"Expected TokenList, got {type(token).__name__}", token)
        token_list = cast(TokenList, token).without_comments()
        if self.splat:
            if len(token_list) <= len(self.rules):
                error(f"Expected more than {len(self.rules)} list items, got {len(token_list)}", token_list)
        elif len(token_list) != len(self.rules):
            error(f"Expected exactly {len(self.rules)} list items, got {len(token_list)}", token_list)
        for rule, token in zip(self.rules, token_list):
            rule.validate(token, error)
        if self.splat:
            remainder = cast(Tuple[Token], token_list[len(self.rules):])
            for token in remainder:
                self.splat.validate(token, error)

    def match(self, token_list:TokenList) -> bool:
        assert(len([r for r in self.rules if type(r) is Exactly]) == 1)
        for rule, token in zip(self.rules, token_list):
            if type(rule) is Exactly:
                if not cast(Exactly, rule).match(token):
                    return False
        return True

    def __repr__(self):
        return "<ListRule>"


class MatchRule(Rule):
    def __init__(self, *rules:ListRule):
        self.rules = rules

    def validate(self, token:Token, error:ErrorCallback):
        token_list = CAST(TokenList, token).without_comments()
        if token_list.is_nil():
            error("Expected non-empty TokenList", token_list)
        for rule in self.rules:
            assert(type(rule) is ListRule)
            if rule.match(token_list):
                return rule.validate(token_list, error)
        error("Unkown expression", token_list)

    def __repr__(self):
        return "<MatchRule>"
