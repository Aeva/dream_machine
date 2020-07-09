
from weakref import ref
from ..handy import *
from .tokens import *
from .parser import Parser
from ..expanders.glsl_types import glsl_builtins


ErrorCallback = Callable[[str, Token], None]


class Syntax:
    """
    Base class for abstract syntax objects, to be filled out by grammar Rule
    objects.

    Subclasses must specify a "rename" class variable, which is used by graph
    parents for placement in attribute lists or dictionaries.

    Subclasses may specify a "primary" class variable, which then denotes an
    attribute within the subclass that should be used as a primary key for
    dictionary lookups within a graph parent.

    Syntax classes are meant to be created by Rule classes upon successful
    validaiton.
    """
    rename = ""
    primary:Optional[str] = None

    def __init__(self, tokens:Optional[TokenList], children, child_types):
        cast(List[Syntax], children)
        cast(List[Type[Syntax]], child_types)
        self.tokens = tokens
        self.children = children
        self.child_types = child_types
        self._keys = dedupe([c.rename for c in child_types])
        self.env:Optional[Program] = None
        self.error_callback:Optional[ErrorCallback] = None
        self.populate(self.children)

    def error(self, hint:str, token:Optional[Token] = None):
        """
        This will generate a nice error message for the user w/ context and
        raise a ValidationError.

        This should only be called from the "rewrite" or "validate" methods
        from subclasses.
        """
        error_callback = cast(ErrorCallback, self.error_callback)
        error_callback(hint, token or CAST(TokenList, self.tokens))

    def populate(self, children):
        for match in self.child_types:
            if match.primary:
                setattr(self, match.rename, {getattr(c, match.primary) : c for c in children if type(c) == match})
            else:
                setattr(self, match.rename, [c for c in children if type(c) == match])

    def subset(self, subset_name):
        subset = getattr(self, subset_name)
        return subset.values() if type(subset) is dict else subset

    def dispatch(self, method_name, *args, **kargs):
        for attr in self._keys:
            for child in self.subset(attr):
                getattr(child, method_name)(*args, **kargs)

    def set_env(self, env, error_callback:ErrorCallback):
        self.env = cast(Program, ref(env))
        self.error_callback = error_callback
        self.dispatch("set_env", env, error_callback)

    def rewrite(self):
        self.dispatch("rewrite")

    def validate(self):
        self.dispatch("validate")

    def report(self):
        msg = ""
        for key in self._keys:
            msg += f".{key}:\n"
            subset = getattr(self, key)
            if type(subset) is dict:
                for primary, child in subset.items():
                    msg += indent(f'"{primary}":\n{indent(child.report())}')
            else:
                for child in subset:
                    msg += indent(child.report())
        return f'{repr(self)}\n{indent(msg)}'

    def __repr__(self):
        return f'<{type(self).__name__}>'


class Struct(Syntax):
    """
    This represents a struct type definition, which may be used to generate GLSL
    structs, GLSL uniform blocks, C++ structs, and C++ side buffer upload functions.
    """
    rename = "structs"
    primary = "name"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        struct, self.name = map(str, cast(TokenList, self.tokens)[:2])
        self.referenced:List[str] = []

    def validate(self):
        Syntax.validate(self)
        if self.name in glsl_builtins:
            self.error(f'Struct cannot be named after built in type "{self.name}".')

        names = []
        for member in self.members:
            if member.name in names:
                self.error(f'Struct "{self.name}" contains more than one member named "{member.name}".')
            else:
                names.append(member.name)
            if member.type == self.name:
                member.error(f"Struct members can't use the type of the struct it belongs to.")
            if member.type in self.env().structs and member.type not in self.referenced:
                self.referenced.append(member.type)

    def __repr__(self):
        return f'<Struct {self.name}>'


class StructMember(Syntax):
    """
    Describes a single member variable within a Struct.
    """
    rename = "members"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        self.type, self.name = map(str, cast(TokenList, self.tokens))

    def validate(self):
        Syntax.validate(self)
        if self.type not in glsl_builtins and self.type not in self.env().structs:
            self.error(f'Undefined type name: "{self.type}"')

    def __repr__(self):
        return f'<StructMember {self.name} {self.type}>'


class Sampler(Syntax):
    """
    This describes a sampler object.  There will be one sampler created for each
    instance of this class.
    """
    rename = "samplers"
    primary = "name"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        sampler, self.name = map(str, cast(TokenList, self.tokens)[:2])

    def validate(self):
        Syntax.validate(self)
        if not self.filters.get("min"):
            self.error("Sampler must specify it's \"min\" filter.")
        if not self.filters.get("mag"):
            self.error("Sampler must specify it's \"mag\" filter.")

    def __repr__(self):
        return f'<Sampler {self.name}>'


class SamplerFilter(Syntax):
    """
    Sampler filter parameters.
    """
    rename = "filters"
    primary = "name"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        self.name, self.value = map(str, cast(TokenList, self.tokens))

    def validate(self):
        Syntax.validate(self)
        supported = ["GL_NEAREST", "GL_LINEAR"]
        if self.value not in supported:
            self.error(f'Unsupported sampler filter value: "{self.value}"')

    def __repr__(self):
        return f'<SamplerFilter {self.name} {self.value}>'


class Format(Syntax):
    """
    This describes the semantic usage of a texture.  This will not result in
    any code generation on its own.  Pipeline definitions will use this to
    produce texture binding points, and Textures will need this information
    for determining what to allocate.  This is also used to map from texture
    instances to samplers.
    """
    rename = "formats"
    primary = "name"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        format, self.name, self.target, self.format, self.sampler = map(str, cast(TokenList, self.tokens))

    def validate(self):
        Syntax.validate(self)
        if self.target != "GL_TEXTURE_2D":
            self.error(f'Unsupported texture target: "{self.target}"')
        if self.format != "GL_RGBA8":
            self.error(f'Unsupported texture format: "{self.format}"')
        if self.sampler not in self.env().samplers:
            self.error(f'Unknown sampler: "{self.sampler}"')
        if self.name in self.env().structs:
            self.error(f'There cannot be a format named "{self.name}", because there is already a struct of the same name.')

    def __repr__(self):
        return f'<Format {self.name} {self.target} {self.format} {self.sampler}>'


class Pipeline(Syntax):
    """
    This represents the pipeline state needed for a draw call.
    This specifies shaders, data interfaces, and fixed function state.
    """
    rename = "pipelines"
    primary = "name"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        pipeline, self.name = map(str, cast(TokenList, self.tokens)[:2])
        self.bindings:List[str] = []

    def rewrite(self):
        Syntax.rewrite(self)
        new_children = []
        for child in self.children:
            if type(child) is PipelineCopy:
                target = cast(PipelineCopy, child).target
                if target == self.name:
                    child.error("A pipeline can't copy itself!")
                found = self.env().pipelines.get(target)
                if found:
                    new_children += found.children
            else:
                new_children.append(child)
        self.populate(new_children)
        for interface in self.interfaces.values():
            if interface.name in self.bindings:
                self.error(f'Pipeline "{self.name}" contains more than one interface named "{interface.name}".')
            self.bindings.append(interface.name)

    def validate(self):
        Syntax.validate(self)
        if "cs" in self.shaders:
            if len(self.shaders.keys()) > 1:
                self.error("Compute pipelines can't use non-compute shaders.")
        else:
            if "vs" not in self.shaders:
                self.error("Raster pipelines must declare a vertex shader.")
            if "fs" not in self.shaders:
                self.error("Raster pipelines must declare a fragment shader.")

    def __repr__(self):
        return f'<Pipeline {self.name}>'


class PipelineShader(Syntax):
    """
    A path to a shader to be used by a pipeline.
    """
    rename = "shaders"
    primary = "type"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        self.type, self.path = map(str, cast(TokenList, self.tokens))

    def __repr__(self):
        return f'<PipelineShader {self.type} "{self.path}">'


class PipelineUse(Syntax):
    """
    Indicates that a given struct should be present in the GLSL sources used
    by the pipeline.
    """
    rename = "structs"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        use, self.struct = map(str, cast(TokenList, self.tokens))

    def validate(self):
        Syntax.validate(self)
        if self.struct not in self.env().structs:
            self.error(f'Unknown struct "{self.struct}"')

    def __repr__(self):
        return f'<PipelineUse {self.struct}>'


class PipelineInterface(Syntax):
    """
    Defines a uniform block or a texture binding point to be used in the
    pipeline's shaders.
    """
    rename = "interfaces"
    primary = "name"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        interface, self.name, self.type = map(str, cast(TokenList, self.tokens))
        self.is_texture = False
        self.is_uniform = False

    def rewrite(self):
        Syntax.rewrite(self)
        self.is_texture = self.type in self.env().formats
        self.is_uniform = self.type in self.env().structs

    def validate(self):
        Syntax.validate(self)
        if not (self.is_texture or self.is_uniform):
            self.error(f'Unknown texture or struct type: "{self.type}"')
        # strictly speaking it should be an error to be both, but it is more useful
        # for it to be an error to have a struct and a format of the same name.

    def __repr__(self):
        return f'<PipelineInterface {self.name} {self.type}>'


class PipelineFlag(Syntax):
    """
    Fixed function state.
    """
    rename = "flags"
    primary = "flag"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        self.state, self.flag = map(str, cast(TokenList, self.tokens))

    def __repr__(self):
        return f'<PipelineFlag {self.flag} = {self.state == "enable"}>'


class PipelineCopy(Syntax):
    """
    This copies in all of the commands from another pipeline.  Commands are
    taken in order, and the last command of a given type is the one that is used.
    """
    rename = "copies"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        copy, self.target = map(str, cast(TokenList, self.tokens))

    def validate(self):
        Syntax.validate(self)
        if self.target not in self.env().pipelines:
            self.error(f'Unknown pipeline copy target: "{self.target}"')

    def __repr__(self):
        return f'<PipelineCopy {self.target}>'


class Buffer(Syntax):
    """
    This corresponds to a buffer object, and is used for binding and upload
    machinery.
    """
    rename = "buffers"
    primary = "handle"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        buffer, self.handle, self.struct = map(str, cast(TokenList, self.tokens))

    def validate(self):
        Syntax.validate(self)
        if self.handle in self.env().samplers:
            self.error(f'Buffer cannot be named "{self.handle}", because there is already a sampler of the same name.')
        if self.struct not in self.env().structs:
            self.error(f'Unknown struct: "{self.struct}"')

    def __repr__(self):
        return f'<Buffer {self.handle} {self.struct}>'


class Texture(Syntax):
    """
    This corresponds to a texture object, and is used for binding and upload
    machinery.
    """
    rename = "textures"
    primary = "handle"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        buffer, self.handle, self.format = map(str, cast(TokenList, self.tokens))

    def validate(self):
        Syntax.validate(self)
        if self.handle in self.env().samplers:
            self.error(f'Texture cannot be named "{self.handle}", because there is already a sampler of the same name.')
        if self.handle in self.env().buffers:
            self.error(f'Texture cannot be named "{self.handle}", because there is already a buffer of the same name.')
        if self.format not in self.env().formats:
            self.error(f'Unknown format: "{self.format}"')

    def __repr__(self):
        return f'<Texture {self.handle} {self.format}>'


class Renderer(Syntax):
    """
    This defines one of your application's renderers, which essentially is the
    specification for what is to be rendered in a given frame.  Only one
    renderer is used per frame, but the renderer can be changed between frames.
    """
    rename = "renderer"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        renderer, self.name = map(str, cast(TokenList, self.tokens)[:2])

    def __repr__(self):
        return f'<Renderer {self.name}>'


class RendererUpdate(Syntax):
    """
    This specifies that a given handle should be updated with user data.
    """
    rename = "updates"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        update, self.resource = map(str, cast(TokenList, self.tokens))

    def validate(self):
        Syntax.validate(self)
        if self.resource not in self.env().textures and self.resource not in self.env().buffers:
            self.error(f'Unknown texture or buffer: "{self.resource}"')

    def __repr__(self):
        return f'<RendererUpdate {self.resource}>'


class RendererDraw(Syntax):
    """
    A draw call.
    """
    rename = "draws"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        draw, self.pipeline = map(str, cast(TokenList, self.tokens)[:2])

    def validate(self):
        Syntax.validate(self)

        # verify that the referenced pipeline exists
        if self.pipeline not in self.env().pipelines:
            self.error(f'Unknown pipeline: "{self.pipeline}"')
        pipeline = self.env().pipelines[self.pipeline]

        # verify the draw's bindings against the referenced pipeline
        for bind in self.binds:

            # the pipeline should reference an interface within the pipeline
            if bind.binding not in pipeline.bindings:
                bind.error(f'Binding "{bind.binding}" is not an interface in this draw\'s pipeline.  See pipeline "{self.pipeline}."')

            # check the binding against the referenced pipeline
            interface:PipelineInterface = pipeline.interfaces[bind.binding]
            if interface.is_uniform:
                # the interface is a uniform block
                if bind.is_texture:
                    bind.error("Cannot bind a texture to a uniform buffer block.")
                elif bind.is_sampler:
                    bind.error("Cannot bind a sampler to a uniform buffer block.")
                else:
                    assert(bind.is_buffer)
                    buffer = self.env().buffers[bind.resource]
                    if buffer.struct != interface.type:
                        bind.error(f'Buffer is type "{buffer.struct}", but the interface expects "{interface.type}"')
            else:
                # the interface is a texture unit
                assert(interface.is_texture)
                if bind.is_buffer:
                    bind.error("Cannot bind a buffer to a texture unit.")
                elif bind.is_texture:
                    texture = self.env().textures[bind.resource]
                    if texture.format != interface.type:
                        # TODO: really we just care if the target is compatible, and maybe if the channels are the same
                        bind.error(f'Texture is format "{texture.format}", but the interface expects "{interface.type}"')
                else:
                    assert(bind.is_sampler)

    def __repr__(self):
        return f'<RendererDraw {self.pipeline}>'


class RendererDrawBind(Syntax):
    """
    A resource binding for a draw call.
    """
    rename = "binds"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        bind, self.binding, self.resource = map(str, cast(TokenList, self.tokens))
        self.is_sampler = False
        self.is_texture = False
        self.is_buffer = False

    def rewrite(self):
        Syntax.rewrite(self)
        self.is_sampler = self.resource in self.env().samplers
        self.is_texture = self.resource in self.env().textures
        self.is_buffer = self.resource in self.env().buffers
        if not (self.is_sampler or self.is_texture or self.is_buffer):
            self.error(f'Unknown texture, buffer, or sampler: "{self.resource}"')

    def __repr__(self):
        return f'<RendererDrawBind {self.binding}, {self.resource}>'


class Program(Syntax):
    """
    This is the syntax graph root, and represents everything within your program.
    """
    rename = "programs"

    def __init__(self, error_handler:ErrorCallback, *args, **kargs):
        Syntax.__init__(self, None, *args, **kargs)
        self.set_env(self, error_handler)
        self.rewrite()
        self.validate()


class Rule:
    """
    Base class for grammar validation rules.
    """
    def constructors(self) -> List[type]:
        return []

    def validate(self, token:Token, error:ErrorCallback) -> Optional[Syntax]:
        raise NotImplementedError
        return False


class AtomRule(Rule):
    """
    Matches a token when the token is not a TokenList or TokenComment.
    """
    def __init__(self, hint:str, atom:type):
        self.hint = hint
        self.atom = atom

    def validate(self, token:Token, error:ErrorCallback) -> Optional[Syntax]:
        if not type(token) == self.atom:
            error(f"Expected {self.hint} to be a {self.atom}, got {type(token).__name__}", token)
        return None

    def __repr__(self):
        return f'<{type(self).__name__} "{self.hint}">'


class WordRule(AtomRule):
    """
    Matches a single TokenWord.
    """
    def __init__(self, hint:str):
        AtomRule.__init__(self, hint, TokenWord)


class StringRule(AtomRule):
    """
    Matches a single TokenString.
    """
    def __init__(self, hint:str):
        AtomRule.__init__(self, hint, TokenString)


class NumberRule(AtomRule):
    """
    Matches a single TokenNumber.
    """
    def __init__(self, hint:str):
        AtomRule.__init__(self, hint, TokenNumber)


class Exactly(WordRule):
    """
    Matches a single TokenWord where the token's vaule is exactly equal to the
    specified value.
    """
    def __init__(self, name:str):
        WordRule.__init__(self, name)

    def validate(self, token:Token, error:ErrorCallback) -> Optional[Syntax]:
        WordRule.validate(self, token, error)
        if str(token) != self.hint:
            error(f"Expected {self.hint}, got {str(token)}...?", token)
        return None

    def match(self, token:Token) -> bool:
        if type(token) == TokenWord:
            return str(token) == self.hint
        else:
            return False

    def __repr__(self):
        return f'<Exactly "{self.name}">'


class ListRule(Rule):
    """
    Matches a sequence of rules within a TokenList.  When successfully validated,
    this will produce syntax objects.  This is typically used within a MatchRule,
    but may also be used as a splat.  Each instance must specify what Syntax type
    will be created, in addition to the rules list etc.
    """
    def __init__(self, construct:Type[Syntax], *rules:Rule, SPLAT:Optional[Rule] = None):
        self.construct = construct
        self.rules = rules
        self.splat = SPLAT

    def constructors(self) -> List[type]:
        return [self.construct]

    def validate(self, token:Token, error:ErrorCallback) -> Optional[Syntax]:
        if type(token) is not TokenList:
            error(f"Expected TokenList, got {type(token).__name__}", token)
        token_list = cast(TokenList, token).without_comments()
        if self.splat:
            if len(token_list) <= len(self.rules):
                error(f"Expected more than {len(self.rules)} list items, got {len(token_list)}", token_list)
        elif len(token_list) != len(self.rules):
            error(f"Expected exactly {len(self.rules)} list items, got {len(token_list)}", token_list)
        children:List[Syntax] = []
        child_types = []
        for rule, token in zip(self.rules, token_list):
            syntax = rule.validate(token, error)
            if syntax:
                children.append(syntax)
        if self.splat:
            remainder = cast(Tuple[Token], token_list[len(self.rules):])
            child_types = self.splat.constructors()
            for token in remainder:
                syntax = self.splat.validate(token, error)
                children.append(cast(Syntax, syntax))
        return self.construct(token_list, children, child_types)

    def match(self, token_list:TokenList) -> bool:
        assert(len([r for r in self.rules if type(r) is Exactly]) == 1)
        assert(type(self.rules[0]) is Exactly)
        for rule, token in zip(self.rules, token_list):
            if type(rule) is Exactly:
                if not cast(Exactly, rule).match(token):
                    return False
        return True

    def __repr__(self):
        return "<ListRule>"


class MatchRule(Rule):
    """
    This will attempt to match a TokenList to one of the associated ListRule
    parameters.
    """
    def __init__(self, *rules:ListRule):
        self.rules = rules

    def constructors(self) -> List[type]:
        return [rule.construct for rule in self.rules]

    def validate(self, token:Token, error:ErrorCallback) -> Optional[Syntax]:
        token_list = CAST(TokenList, token).without_comments()
        if token_list.is_nil():
            error("Expected non-empty TokenList", token_list)
        for rule in self.rules:
            assert(type(rule) is ListRule)
            if rule.match(token_list):
                return rule.validate(token_list, error)
        error("Unkown expression", token_list)
        return None

    def __repr__(self):
        return "<MatchRule>"


GRAMMAR = MatchRule(
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
        ListRule(PipelineCopy, Exactly("copy"), WordRule("draw name")))),
    ListRule(Buffer, Exactly("buffer"), WordRule("buffer name"), WordRule("buffer type")),
    ListRule(Texture, Exactly("texture"), WordRule("texture name"), WordRule("texture type")),
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

    def grammar_error(hint:str, token:Token):
        message = parser.message(hint, *token.pos(), *token.pos())
        raise GrammarError(message)

    def validation_error(hint:str, token:Token):
        message = parser.message(hint, *token.pos(), *token.pos())
        raise ValidationError(message)

    tokens = parser.parse()
    children:List[Syntax] = []
    for token in tokens:
        if type(token) is not TokenComment:
            token = CAST(TokenList, token)
            children.append(cast(Syntax, GRAMMAR.validate(token, grammar_error)))

    return Program(validation_error, children, GRAMMAR.constructors())
