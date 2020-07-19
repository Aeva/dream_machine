
import re
from .abstract import *
from .rules import *


def MatchSplat(pattern):
    return MatchRule(*[rule for (name,rule) in globals().items() if re.match(pattern, name)])


STRUCT_RULE = \
    ListRule(Struct, Exactly("struct"), WordRule("struct name"),
             SPLAT = ListRule(StructMember, WordRule("type"), WordRule("name")))


FORMAT_RULE = \
    ListRule(Format, Exactly("format"), WordRule("format name"), WordRule("texture target"),
             WordRule("texture format"), WordRule("sampler name"))


USER_VAR_RULE = \
    ListRule(UserVar, Exactly("uservar"), WordRule("ctype"), WordRule("name"), ArithmeticRule())


SAMPLER_MIN_RULE = ListRule(SamplerFilter, Exactly("min"), WordRule("opengl filter enum"))

SAMPLER_MAG_RULE = ListRule(SamplerFilter, Exactly("mag"), WordRule("opengl filter enum"))

SAMPLER_RULE = \
    ListRule(Sampler, Exactly("sampler"), WordRule("sampler name"),
             SPLAT = MatchSplat(r'SAMPLER_[A-Z]+?_RULE'))


PIPELINE_VS_RULE = ListRule(PipelineShader, Exactly("vs"), StringRule("shader path"))

PIPELINE_FS_RULE = ListRule(PipelineShader, Exactly("fs"), StringRule("shader path"))

PIPELINE_USE_RULE = ListRule(PipelineUse, Exactly("use"), WordRule("struct or interface or texture name"))

PIPELINE_INTERFACE_RULE = ListRule(PipelineInterface, Exactly("interface"), WordRule("interface name"), WordRule("interface type"))

PIPELINE_ENABLE_RULE = ListRule(PipelineFlag, Exactly("enable"), WordRule("opengl capability enum"))

PIPELINE_DISABLE_RULE = ListRule(PipelineFlag, Exactly("disable"), WordRule("opengl capability enum"))

PIPELINE_COPY_RULE = ListRule(PipelineCopy, Exactly("copy"), WordRule("draw name"))

PIPELINE_OUT_RULE = ListRule(PipelineAttachments, Exactly("out"), SPLAT = WordRule("texture name"))

PIPELINE_RULE = ListRule(Pipeline, Exactly("pipeline"), WordRule("draw name"),
                         SPLAT = MatchSplat(r'PIPELINE_[A-Z]+?_RULE'))


BUFFER_RULE = ListRule(Buffer, Exactly("buffer"), WordRule("buffer name"), WordRule("buffer type"))


TEXTURE_SRC_RULE = ListRule(TextureSrc, Exactly("src"), StringRule("image path"))

TEXTURE_WIDTH_RULE = ListRule(TextureDimension, Exactly("width"), ArithmeticRule())

TEXTURE_HEIGHT_RULE = ListRule(TextureDimension, Exactly("height"), ArithmeticRule())

TEXTURE_DEPTH_RULE = ListRule(TextureDimension, Exactly("depth"), ArithmeticRule())

TEXTURE_RULE = \
    ListRule(Texture, Exactly("texture"), WordRule("texture name"), WordRule("texture type"),
             SPLAT = MatchSplat(r'TEXTURE_[A-Z]+?_RULE'))


RENDERER_UPDATE_RULE = ListRule(RendererUpdate, Exactly("update"), WordRule("handle name"))

RENDERER_DRAW_RULE = ListRule(RendererDraw, Exactly("draw"), WordRule("draw name"),
                              SPLAT = MatchRule(ListRule(RendererDrawBind, Exactly("bind"), WordRule("binding point"), WordRule("handle name"))))

RENDERER_RULE = \
    ListRule(Renderer, Exactly("renderer"), WordRule("renderer name"),
             SPLAT = MatchSplat(r'RENDERER_[A-Z]+?_RULE'))


GRAMMAR = MatchRule(
    USER_VAR_RULE,
    STRUCT_RULE,
    BUFFER_RULE,
    FORMAT_RULE,
    SAMPLER_RULE,
    TEXTURE_RULE,
    PIPELINE_RULE,
    RENDERER_RULE)


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
