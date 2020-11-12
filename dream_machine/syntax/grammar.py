
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


import re
from .abstract import *
from .rules import *


def MatchSplat(pattern, fnord=False):
    return MatchRule(*[rule for (name,rule) in globals().items() if re.match(pattern, name)])


META_BACKEND_RULE = \
    ListRule(Backend, Exactly("backend"), WordRule("name"))


STRUCT_MEMBER_ARRAY_RULE = \
    ListRule(StructMember, WordRule("name"), Exactly("array"), NumberRule("array size"), WordRule("type"))

STRUCT_MEMBER_RULE = \
    ListRule(StructMember, WordRule("name"), WordRule("type"))

STRUCT_RULE = \
    ListRule(Struct, Exactly("struct"), WordRule("struct name"),
             SPLAT = MatchSplat(r'STRUCT_MEMBER[A-Z_]*?_RULE', fnord=True))


FORMAT_RULE = \
    ListRule(Format, Exactly("format"), WordRule("format name"), WordRule("texture target"),
             WordRule("texture format"), WordRule("sampler name"))


USER_VAR_RULE = \
    ListRule(UserVar, Exactly("uservar"), WordRule("ctype"), WordRule("name"), ArithmeticRule("value"))


SAMPLER_MIN_RULE = ListRule(SamplerFilter, Exactly("min"), WordRule("opengl filter enum"))

SAMPLER_MAG_RULE = ListRule(SamplerFilter, Exactly("mag"), WordRule("opengl filter enum"))

SAMPLER_RULE = \
    ListRule(Sampler, Exactly("sampler"), WordRule("sampler name"),
             SPLAT = MatchSplat(r'SAMPLER_[A-Z]+?_RULE'))


PIPELINE_VS_RULE = ListRule(PipelineShader, Exactly("vs"), StringRule("shader path"))

PIPELINE_FS_RULE = ListRule(PipelineShader, Exactly("fs"), StringRule("shader path"))

PIPELINE_CS_RULE = ListRule(PipelineShader, Exactly("cs"), StringRule("shader path"))

PIPELINE_USE_RULE = ListRule(PipelineUse, Exactly("use"), WordRule("struct or interface or texture name"))

PIPELINE_ENABLE_RULE = ListRule(PipelineFlag, Exactly("enable"), WordRule("opengl capability enum"))

PIPELINE_DISABLE_RULE = ListRule(PipelineFlag, Exactly("disable"), WordRule("opengl capability enum"))

PIPELINE_COPY_RULE = ListRule(PipelineCopy, Exactly("copy"), WordRule("draw name"))

PIPELINE_IN_RULE = ListRule(PipelineInput, Exactly("in"), WordRule("resource name"))

PIPELINE_OUT_RULE = ListRule(PipelineOutput, Exactly("out"), WordRule("resource name"))

PIPELINE_SIDE_RULE = ListRule(PipelineSideput, Exactly("side"), WordRule("resource name"))

PIPELINE_RULE = ListRule(Pipeline, Exactly("pipeline"), WordRule("draw name"),
                         SPLAT = MatchSplat(r'PIPELINE_[A-Z]+?_RULE'))


BUFFER_RULE = ListRule(Buffer, Exactly("buffer"), WordRule("buffer name"), WordRule("buffer type"))


TEXTURE_SRC_RULE = ListRule(TextureSrc, Exactly("src"), StringRule("image path"))

TEXTURE_CLEAR_RULE = ListRule(TextureClearColor, Exactly("clear"), NumberRule("red"), NumberRule("green"), NumberRule("blue"), NumberRule("alpha"))

TEXTURE_WIDTH_RULE = ListRule(TextureDimension, Exactly("width"), ArithmeticRule("value"))

TEXTURE_HEIGHT_RULE = ListRule(TextureDimension, Exactly("height"), ArithmeticRule("value"))

TEXTURE_DEPTH_RULE = ListRule(TextureDimension, Exactly("depth"), ArithmeticRule("value"))

TEXTURE_RULE = \
    ListRule(Texture, Exactly("texture"), WordRule("texture name"), WordRule("texture type"),
             SPLAT = MatchSplat(r'TEXTURE_[A-Z]+?_RULE'))


RENDERER_UPDATE_RULE = ListRule(RendererUpdate, Exactly("update"), WordRule("handle name"))

RENDERER_DRAW_RULE = ListRule(RendererDraw, Exactly("draw"), WordRule("pipeline name"))

RENDERER_DISPATCH_RULE = ListRule(RendererDispatch, Exactly("dispatch"), WordRule("pipeline name"), ArithmeticRule("x"), ArithmeticRule("y"), ArithmeticRule("z"))

RENDERER_NEXT_RULE = ListRule(RendererNext, Exactly("next"), WordRule("renderer name"))

RENDERER_RULE = \
    ListRule(Renderer, Exactly("renderer"), WordRule("renderer name"),
             SPLAT = MatchSplat(r'RENDERER_[A-Z]+?_RULE'))


GRAMMAR = MatchRule(
    META_BACKEND_RULE,
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
