
import os
import string
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
        return f"<TokenString at {self.line}:{self.col} → \"{self.text}\">"

    def __str__(self) -> str:
        return self.text

    def pretty(self) -> str:
        return f"{self.quote}{str(self)}{self.quote}"


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


class ParserError(Exception):
    pass


class Parser:
    """
    Implements a parser for a pseudo-lisp dsl.
    """

    def __init__(self):
        self.path:str = ""
        self.raw:str = ""
        self.char:str = ""
        self.text:str = ""
        self.reset()

    def open(self, path):
        """
        Set a specific file as the target for parsing.
        """
        self.path = path
        with open(path, "r") as src:
            self.raw:str = src.read()
        self.reset()

    def reset(self, raw:Optional[str]= None):
        """
        Reset the parser to the beginning of the file, and optionally provide
        a string to override what is being parsed.  Used for debugging and testing.
        """
        if raw is not None:
            self.raw = raw
        if len(self.raw) > 0:
            self.char = self.raw[0]
            self.text = self.raw[1:]
        else:
            self.char = ""
            self.text = ""
        self.line = 0
        self.col = 0

    def error(self, hint:str, start_line:Optional[int] = None, start_col:Optional[int] = None):
        """
        Provide a nice error for the user when the parser fails.
        """
        start_line = start_line or max(self.line - 1, 0)
        assert(start_line <= self.line)

        margin = len(str(self.line)) + 3
        def prefix(n):
            """
            Generates a nice left-padded line number prefix.
            """
            pre = f"{start_line + n}: "
            pad = margin - len(pre)
            return (" " * pad) + pre

        lines = self.raw.split("\n")[start_line:self.line+1]
        message = f"\n\n{hint} in file \"{self.path}\" near line {self.line} column {self.col}:\n"

        for index, line in enumerate(lines):
            message += prefix(index)
            if line != lines[-1]:
                # rewrite tabs as spaces
                message += line.replace("\t", "    ") + "\n"
            else:
                # rewrite tabs as spaces and adjust cursor position
                tabs = line[:self.col].count("\t")
                ext = tabs * 3
                message += line.replace("\t", "    ") + "\n"
                message += (" " * (self.col + ext + margin)) + "↑\n"
        raise ParserError(message)

    def advance(self):
        """
        Advance the parser's cursor.  Not meant to be called externally.
        """
        assert(self.char != "EOF")
        if self.char == "\n":
            self.line += 1
            self.col = 0
        else:
            self.col += 1
        if len(self.text) > 0:
            self.char = self.text[0]
            self.text = self.text[1:]
        else:
            self.char = "EOF"

    def pos(self) -> Tuple[int, int]:
        """
        Returns the parser's current cursor position.
        """
        return self.line, self.col

    def parse_number(self) -> TokenNumber:
        """
        Attempt to parse a numeric token.
        """
        assert(self.char in "-." + string.digits)
        pos = self.pos()
        acc = ""
        decimal = False
        while True:
            if acc == "" and self.char == "-":
                acc += self.char
            elif self.char in string.digits:
                acc += self.char
            elif self.char == "." and not decimal:
                if acc in ["", "-"]:
                    acc += "0"
                acc += self.char
                decimal = True
            else:
                break;
            self.advance()
        value = float(acc) if decimal else int(acc)
        return TokenNumber(acc, value, *pos)

    def parse_word(self) -> TokenWord:
        """
        Attempt to parse an identifier token.
        """
        assert(self.char in string.ascii_letters + "_")
        pos = self.pos()
        acc = ""
        valid = string.ascii_letters + string.digits + "_"
        while self.char in valid:
            acc += self.char
            self.advance()
        return TokenWord(acc, *pos)

    def parse_string(self) -> TokenString:
        """
        Attempt to parse a string token.
        """
        pos = self.pos()
        term = self.char
        self.advance()
        acc = ""
        while True:
            if self.char == "\\":
                self.advance()
                if self.char in (term, "\\"):
                    acc += self.char
                else:
                    acc += "\\"
                    acc += self.char
                self.advance()
                continue
            if self.char == term:
                self.advance()
                break
            acc += self.char
            self.advance()
        return TokenString(term, acc, *pos)

    def skip_whitespace(self):
        """
        Seek past whitespace.
        """
        assert(self.char in string.whitespace)
        while self.char in string.whitespace:
            self.advance()

    def parse_comment(self) -> TokenComment:
        """
        Attempt to parse a comment token.
        """
        assert(self.char == ";")
        pos = self.pos()
        self.advance()
        acc = ""
        while not self.char in ["\n", "EOF"]:
            acc += self.char
            self.advance()
        if self.char == "\n":
            self.advance()
        return TokenComment(acc, *pos)

    def parse_expression(self) -> TokenList:
        """
        Attempt to parse a token list.
        """
        assert(self.char == "(")
        pos = self.pos()
        self.advance()
        tokens:List[Token] = []
        separator_needed = False
        separators = string.whitespace + ";()"
        atoms = ".-_" + string.digits + string.ascii_letters + "'" + '"'
        while True:
            if self.char in separators:
                # things that count as separators
                separator_needed = False
                if self.char in string.whitespace:
                    # whitespace
                    self.skip_whitespace()
                elif self.char == ";":
                    # comment
                    tokens.append(self.parse_comment())
                elif self.char == "(":
                    # begin list
                    tokens.append(self.parse_expression())
                elif self.char == ")":
                    # end list
                    self.advance()
                    break
                else:
                    # should be unreachable
                    self.error("parser bug?", 0, 0)
            elif self.char in atoms:
                # atoms
                if separator_needed:
                    self.error("Invalid literal")
                separator_needed = True
                if self.char in [".-"] or self.char in string.digits:
                    # numbers
                    tokens.append(self.parse_number())
                elif self.char in string.ascii_letters or self.char == "_":
                    # words
                    tokens.append(self.parse_word())
                elif self.char in ["'", '"']:
                    # strings
                    tokens.append(self.parse_string())
                else:
                    # should be unreachable
                    self.error("parser bug?", 0, 0)
            else:
                # unexpected
                self.error(f"Unexpected char \"{self.char}\"", *pos)
        return TokenList(tuple(tokens), *pos)

    def parse(self) -> Tuple[Token, ...]:
        """
        Parse everything and return a list of tokens.
        """
        tokens:List[Token] = []
        while self.char != "EOF":
            if self.char in string.whitespace:
                self.skip_whitespace()
            elif self.char == ";":
                tokens.append(self.parse_comment())
            elif self.char == "(":
                tokens.append(self.parse_expression())
            else:
                self.error(f"Unexpected char \"{self.char}\"")
        self.reset()
        return tuple(tokens)
