
from .intermediary import *
from ..syntax.parser import ParserError
from ..syntax.grammar import GRAMMAR
from ..syntax.validator import validate_grammar


def run(source:str) -> Program:
    """
    Setup code common to the tests in this file.
    """
    parser = Parser()
    parser.reset(source)
    tokens = parser.parse()
    validate_grammar(GRAMMAR, parser, tokens)
    program = Program(parser)
    program.process(tokens)
    return program


def bogus(expected, source:str):
    """
    Raises if the expection "expected" is not raised by parsing or
    validation.
    """
    raised = False
    try:
        run(source)
    except expected:
        raised = True
    assert(raised)


def test_valid_sampler():
    """
    A sampler with both min_filter and mag_filter set correctly.
    """
    src = """
(sampler SomeSampler
	(min_filter GL_NEAREST)
	(mag_filter GL_LINEAR))
"""
    program = run(src)
    assert("SomeSampler" in program.samplers)
    sampler = program.samplers["SomeSampler"]
    assert(sampler.min_filter == "GL_NEAREST")
    assert(sampler.mag_filter == "GL_LINEAR")


def test_sampler_with_no_parameters():
    """
    A sampler with no parameters.
    """
    src = "(sampler SomeSampler)"
    bogus(ParserError, src)


def test_sampler_with_no_mag_filter():
    """
    A sampler with only the min filter set.
    """
    src = """
(sampler SomeSampler
    (min_filter GL_NEAREST))
"""
    bogus(ParserError, src)


def test_sampler_mith_bogus_mag_filter():
    """
    A sampler with only the mag filter set.
    """
    src = """
(sampler SomeSampler
    (mag_filter GL_NEAREST))
"""
    bogus(ParserError, src)


def test_sampler_mith_bogus_min_filter():
    """
    A sampler with bogus filter values.
    """
    src = """
(sampler SomeSampler
	(min_filter fake_filter_enum)
	(mag_filter aoeantoheantsohe))
"""
    bogus(ParserError, src)


def test_duplicate_sampler():
    """
    Should throw an error when there is a duplicate sampler definition.
    """
    src = """
(sampler SomeSampler
	(min_filter GL_NEAREST)
	(mag_filter GL_LINEAR))
(sampler SomeSampler
	(min_filter GL_NEAREST)
	(mag_filter GL_LINEAR))
"""
    bogus(ParserError, src)


def test_valid_texture2d():
    """
    Minimal texture2d setup.
    """
    src = """
(sampler SomeSampler
	(min_filter GL_NEAREST)
	(mag_filter GL_LINEAR))

(texture2d SomeTexture
    (use SomeSampler)
    (format RGBA8))
"""
    program = run(src)
    assert("SomeTexture" in program.textures)
    texture = program.textures["SomeTexture"]
    assert(texture.format == "RGBA8")
    assert(texture.sampler == "SomeSampler")


def test_texture2d_with_missing_sampler():
    """
    A texture with missing params.
    """
    src = """
(texture2d SomeTexture
    (format RGBA8))
"""
    bogus(ParserError, src)


def test_texture2d_with_missing_format():
    """
    A texture with missing params.
    """
    src = """
(sampler SomeSampler
	(min_filter GL_NEAREST)
	(mag_filter GL_LINEAR))

(texture2d SomeTexture
    (use SomeSampler))
"""
    bogus(ParserError, src)


def test_duplicate_texture2d_definition():
    """
    Duplicate texture definition.
    """
    src = """
(sampler SomeSampler
	(min_filter GL_NEAREST)
	(mag_filter GL_LINEAR))

(texture2d SomeTexture
    (use SomeSampler)
    (format RGBA8))
(texture2d SomeTexture
    (use SomeSampler)
    (format RGBA8))
"""
    bogus(ParserError, src)


def test_texture2d_with_invalid_sampler_reference():
    """
    Invalid sampler reference.
    """
    src = """
(texture2d SomeTexture
    (use SomeSampler)
    (format RGBA8))
"""
    bogus(ParserError, src)


def test_texture2d_with_invalid_texture_format():
    """
    Invalid texture format.
    """
    src = """
(sampler SomeSampler
	(min_filter GL_NEAREST)
	(mag_filter GL_LINEAR))

(texture2d SomeTexture
    (use SomeSampler)
    (format bogus_texture_format))
"""
    bogus(ParserError, src)


def test_preload():
    """
    Valid preload statement.
    """
    src = """
(sampler SomeSampler
	(min_filter GL_NEAREST)
	(mag_filter GL_LINEAR))

(texture2d SomeTexture
    (use SomeSampler)
    (format RGBA8))

(handle SomeHandle SomeTexture)

(preload SomeHandle "fake_path.png")
    """
