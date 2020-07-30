
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


import string
from typing import *
from .tokens import *


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

    def message(self,
                hint:str,
                start_line:Optional[int] = None, start_col:Optional[int] = None,
                end_line:Optional[int] = None, end_col:Optional[int] = None):
        """
        For generating error messages and warnings and so on.
        """
        end_line = end_line or self.line
        end_col = end_col or self.col
        start_line = start_line or max(end_line - 1, 0)
        assert(start_line <= end_line)

        margin = len(str(end_line)) + 3
        def prefix(n):
            """
            Generates a nice left-padded line number prefix.
            """
            pre = f"{start_line + n}: "
            pad = margin - len(pre)
            return (" " * pad) + pre

        lines = self.raw.split("\n")[start_line:end_line+1]
        message = f"\n\n{hint} in file \"{self.path}\" near line {end_line} column {end_col}:\n"

        for index, line in enumerate(lines):
            message += prefix(index)
            if line != lines[-1]:
                # rewrite tabs as spaces
                message += line.replace("\t", "    ") + "\n"
            else:
                # rewrite tabs as spaces and adjust cursor position
                tabs = line[:end_col].count("\t")
                ext = tabs * 3
                message += line.replace("\t", "    ") + "\n"
                message += (" " * (end_col + ext + margin)) + "↑\n"
        return message

    def error(self,
              hint:str, start_line:Optional[int] = None, start_col:Optional[int] = None,
              end_line:Optional[int] = None, end_col:Optional[int] = None):
        """
        Provide a nice error for the user when the parser fails.
        """
        message = self.message(hint, start_line, start_col, end_line, end_col)
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
            if self.char == "EOF":
                self.error("End of file reached while parsing a string", *pos)
            if self.char == "\n":
                self.error("Line end reached while parsing a string", *pos)
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
