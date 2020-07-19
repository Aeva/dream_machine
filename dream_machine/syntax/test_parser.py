
from .tokens import *
from .parser import *


def reset(source:str) -> Parser:
    p = Parser()
    p.reset(source)
    return p


def run(source:str) -> Tuple[Token, ...]:
    return reset(source).parse()


def test_valid_numbers():
    def case(src:str) -> TokenNumber:
        p = reset(src)
        return p.parse_number()

    t = case("1234")
    assert(type(t) is TokenNumber)
    assert(t.value == 1234)
    assert(t.original == "1234")
    assert(str(t) == "1234")

    t = case("3.14")
    assert(type(t) is TokenNumber)
    assert(t.value == 3.14)
    assert(t.original == "3.14")
    assert(str(t) == "3.14")

    t = case("-69.420")
    assert(type(t) is TokenNumber)
    assert(t.value == -69.42)
    assert(t.original == "-69.420")
    assert(str(t) == "-69.42")

    t = case(".25")
    assert(type(t) is TokenNumber)
    assert(t.value == 0.25)
    assert(t.original == "0.25")
    assert(str(t) == "0.25")

    t = case("25.")
    assert(type(t) is TokenNumber)
    assert(t.value == 25.0)
    assert(t.original == "25.")
    assert(str(t) == "25.0")


def test_valid_words():
    def case(src:str) -> TokenWord:
        p = reset(src)
        return p.parse_word()

    t = case("HailEris")
    assert(t.word == "HailEris")
    assert(str(t) == "HailEris")

    t = case("_boop")
    assert(t.word == "_boop")
    assert(str(t) == "_boop")

    t = case("kEySm_AsH1234")
    assert(t.word == "kEySm_AsH1234")
    assert(str(t) == "kEySm_AsH1234")


def test_valid_strings():
    def case(src:str) -> TokenString:
        p = reset(src)
        return p.parse_string()

    t = case('"hello_world"')
    assert(type(t) is TokenString)
    assert(str(t) == "hello_world")
    assert(t.quote == '"')

    t = case("'keysmash'")
    assert(type(t) is TokenString)
    assert(str(t) == "keysmash")
    assert(t.quote == "'")


def test_valid_expressions():
    def case(src:str) -> TokenList:
        p = reset(src)
        return p.parse_expression()

    def validate(t:TokenList, e:tuple):
        assert(type(t) is TokenList)
        assert(len(t) == len(e))
        for a, b in zip(t, e):
            if type(b) is tuple:
                assert(type(a) is TokenList)
                validate(a, b)
            else:
                assert(type(a) is b)

    t = case("(add 1 2 3)")
    validate(t, (TokenWord, TokenNumber, TokenNumber, TokenNumber))

    t = case("(fnorb 'hello world')")
    validate(t, (TokenWord, TokenString))

    t = case("(frob (frob (frob bloop) bloop) ribbit)")
    validate(t, (TokenWord, (TokenWord, (TokenWord, TokenWord), TokenWord), TokenWord))

    t = case("((meep) moop)")
    validate(t, ((TokenWord, ), TokenWord))

    t = case("(1 2 3 (4 5 6))")
    validate(t, (TokenNumber, TokenNumber, TokenNumber, (TokenNumber, TokenNumber, TokenNumber)))
    numbers = tuple([n.value for n in t.tokens[:3]] + [n.value for n in t.tokens[3]])
    assert(numbers == (1, 2, 3, 4, 5, 6))
