
from typing import *


class Token:
    """
    Abstract base class representing a token returned by the parser.
    """
    def __init__(self, line:int, col:int):
        self.line = line
        self.col = col

    def __repr__(self) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        raise NotImplementedError

    def pretty(self) -> str:
        return str(self)

    def pos(self) -> Tuple[int, int]:
        """
        Returns the beginning of the token.
        """
        return self.line, self.col


class TokenNumber(Token):
    """
    A token containing a number.
    """
    def __init__(self, original:str, value:Union[int, float], line:int, col:int):
        Token.__init__(self, line, col)
        self.original = original
        self.value = value

    def __repr__(self) -> str:
        return f"<TokenNumber at {self.line}:{self.col} → {self.original}>"

    def __str__(self) -> str:
        return str(self.value)


class TokenWord(Token):
    """
    A token representing an indentifier.
    """
    def __init__(self, word:str, line:int, col:int):
        Token.__init__(self, line, col)
        self.word = word

    def __repr__(self) -> str:
        return f"<TokenWord at {self.line}:{self.col} → {self.word}>"

    def __str__(self) -> str:
        return self.word


class TokenString(Token):
    """
    A token representing a string.
    """
    def __init__(self, quote:str, text:str, line:int, col:int):
        Token.__init__(self, line, col)
        self.quote = quote
        self.text = text

    def __repr__(self) -> str:
        return f"<TokenString at {self.line}:{self.col} → {self.pretty()}>"

    def __str__(self) -> str:
        return self.text

    def pretty(self) -> str:
        sub = str(self).replace(self.quote, f"\\{self.quote}")
        return f"{self.quote}{sub}{self.quote}"


class TokenComment(Token):
    """
    A token representing a comment.
    """
    def __init__(self, text:str, line:int, col:int):
        Token.__init__(self, line, col)
        self.text = text

    def __repr__(self) -> str:
        return f"<TokenComment at {self.line}:{self.col} → \"{self.text}\">"

    def __str__(self) -> str:
        return self.text

    def pretty(self) -> str:
        return f";{str(self)}"


class TokenList(Token):
    """
    A list of tokens.
    """
    def __init__(self, tokens:Tuple[Token, ...], line:int, col:int):
        Token.__init__(self, line, col)
        self.tokens = tokens

    def is_nil(self):
        return len(self.tokens) == 0

    def without_comments(self):
        """
        Used for validation.
        """
        return TokenList(tuple([t for t in self.tokens if type(t) is not TokenComment]), *self.pos())

    def __len__(self):
        return len(self.tokens)

    def __getitem__(self, key) -> Union[Token,Tuple[Token]]:
        return self.tokens[key]

    def __iter__(self):
        tokens = list(self.tokens)
        while len(tokens) > 0:
            yield tokens.pop(0)

    def __repr__(self) -> str:
        return f"<TokenList at {self.line}:{self.col} → {self.tokens}>"

    def __str__(self) -> str:
        return "(" + " ".join(map(str, self.tokens)) + ")"

    def pretty(self) -> str:
        types = [type(token) for token in self.tokens]
        if types.count(TokenList):
            body = []
            for token in self.tokens:
                if type(token) == TokenList:
                    body += token.pretty().split("\n")
                else:
                    body.append(token.pretty())
            return "(" + "\n    ".join(body) + ")"
        else:
            pretties = [token.pretty() for token in self.tokens]
            return "(" + " ".join(pretties) + ")"