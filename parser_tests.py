
from parser_experiment import *


def number_test():
    def case(text:str, expected:float):
        parser = Parser()
        parser.reset(text)
        token = parser.parse_number()
        assert(type(token) is TokenNumber)
        assert(token.value == expected)
    case("123", 123)
    case("-.123", -0.123)
    case("123.123", 123.123)
    case(".0987", 0.0987)


def word_test():
    parser = Parser()
    parser.reset("B33p_bl0p 123")
    token = parser.parse_word()
    assert(token.word == "B33p_bl0p")


def string_test():
    parser = Parser()
    parser.reset("\"Hello\" \n 'World'")
    token = parser.parse_string()
    assert(token.text == "Hello")
    parser.skip_whitespace()
    token = parser.parse_string()
    assert(token.text == "World")

    parser.reset(r'"Hello \"World\""')
    token = parser.parse_string()
    assert(token.text == 'Hello "World"')


def comment_test():
    parser = Parser()
    parser.reset("; meep\nmoop")
    token = parser.parse_comment()
    assert(token.text == " meep")


def expression_test():
    parser = Parser()
    parser.reset("(Hail _Eris \"hello hello hello\" 123 ; comment)\nsweet)")
    expr = parser.parse_expression()
    expected = \
    [
        TokenWord,
        TokenWord,
        TokenString,
        TokenNumber,
        TokenComment,
        TokenWord
    ]
    assert(len(expr.tokens) == len(expected))
    for token, token_type in zip(expr.tokens, expected):
        assert(type(token) == token_type)

    parser.reset("(disco (recursion (1 2 3) bloop))")
    expr = parser.parse_expression()
    expected = \
    [
        TokenWord,
        TokenList
    ]
    assert(len(expr.tokens) == len(expected))
    for token, token_type in zip(expr.tokens, expected):
        assert(type(token) == token_type)
    expr = expr.tokens[1]
    expected = \
    [
        TokenWord,
        TokenList,
        TokenWord
    ]
    assert(len(expr.tokens) == len(expected))
    for token, token_type in zip(expr.tokens, expected):
        assert(type(token) == token_type)
    expr = expr.tokens[1]
    expected = \
    [
        TokenNumber,
        TokenNumber,
        TokenNumber
    ]
    assert(len(expr.tokens) == len(expected))
    for token, token_type in zip(expr.tokens, expected):
        assert(type(token) == token_type)


def program_test():
    src = """
; some comment


(fnord 1 2 3)
""".strip()
    parser = Parser()
    parser.reset(src)
    tokens = parser.parse()
    expected = \
    [
        TokenComment,
        TokenList
    ]
    assert(len(tokens) == len(expected))
    for token, token_type in zip(tokens, expected):
        assert(type(token) == token_type)


def error_test():
    src = """
; blah blah blah
# <------ INVALID CHARACTER!
""".strip()
    try:
        parser = Parser()
        parser.reset(src)
        parser.parse()
    except ParserError:
        return
    else:
        assert(False)


def integration_test():
    parser = Parser()
    parser.open("example.data")
    tokens = parser.parse()
    for token in tokens:
        if type(token) == TokenList:
            print()
        print(token.pretty())


if __name__ == "__main__":
    number_test()
    word_test()
    string_test()
    comment_test()
    expression_test()
    program_test()
    error_test()
    integration_test()
