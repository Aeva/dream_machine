
from .abstract import *
from .rules import *


GRAMMAR = MatchRule(
    ListRule(UserVar, Exactly("uservar"), WordRule("ctype"), WordRule("name"), ArithmeticRule()),
    ListRule(Struct, Exactly("struct"), WordRule("struct name"), SPLAT = ListRule(StructMember, WordRule("type"), WordRule("name"))),
    ListRule(Sampler, Exactly("sampler"), WordRule("sampler name"), SPLAT = MatchRule(
        ListRule(SamplerFilter, Exactly("min"), WordRule("opengl filter enum")),
        ListRule(SamplerFilter, Exactly("mag"), WordRule("opengl filter enum")))),
    ListRule(Format, Exactly("format"), WordRule("format name"), WordRule("texture target"), WordRule("texture format"), WordRule("sampler name")),
    ListRule(Pipeline, Exactly("pipeline"), WordRule("draw name"), SPLAT = MatchRule(
        ListRule(PipelineShader, Exactly("vs"), StringRule("shader path")),
        ListRule(PipelineShader, Exactly("fs"), StringRule("shader path")),
        ListRule(PipelineUse, Exactly("use"), WordRule("struct or interface or texture name")),
        ListRule(PipelineInterface, Exactly("interface"), WordRule("interface name"), WordRule("interface type")),
        ListRule(PipelineFlag, Exactly("enable"), WordRule("opengl capability enum")),
        ListRule(PipelineFlag, Exactly("disable"), WordRule("opengl capability enum")),
        ListRule(PipelineCopy, Exactly("copy"), WordRule("draw name")),
        ListRule(PipelineAttachments, Exactly("out"), SPLAT = WordRule("texture name")))),
    ListRule(Buffer, Exactly("buffer"), WordRule("buffer name"), WordRule("buffer type")),
    ListRule(Texture, Exactly("texture"), WordRule("texture name"), WordRule("texture type"), SPLAT = MatchRule(
        ListRule(TextureSrc, Exactly("src"), StringRule("image path")),
        ListRule(TextureDimension, Exactly("width"), ArithmeticRule()),
        ListRule(TextureDimension, Exactly("height"), ArithmeticRule()),
        ListRule(TextureDimension, Exactly("depth"), ArithmeticRule()))),
    ListRule(Renderer, Exactly("renderer"), WordRule("renderer name"), SPLAT = MatchRule(
        ListRule(RendererUpdate, Exactly("update"), WordRule("handle name")),
        ListRule(RendererDraw, Exactly("draw"), WordRule("draw name"), SPLAT = MatchRule(
            ListRule(RendererDrawBind, Exactly("bind"), WordRule("binding point"), WordRule("handle name")))))))


class GrammarError(Exception):
    pass


class ValidationError(Exception):
    pass


def validate(parser:Parser):
    """
    Validate the program's tokens against the grammar tree, and then return the
    abstract syntax tree.
    """

    def error_handler(hint:str, token:Token, ErrorType=GrammarError):
        message = parser.message(hint, *token.pos(), *token.pos())
        raise ErrorType(message)

    def validation_error(hint:str, token:Token):
        error_handler(hint, token, ValidationError)

    tokens = parser.parse()
    children:List[Syntax] = []
    for token in tokens:
        if type(token) is not TokenComment:
            token = CAST(TokenList, token)
            children.append(cast(Syntax, GRAMMAR.validate(token, error_handler)))

    return Program(validation_error, children, GRAMMAR.constructors())
