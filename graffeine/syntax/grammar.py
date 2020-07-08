
from weakref import ref
from ..handy import *
from .tokens import *
from .parser import Parser


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
        self.env = None
        self.populate(self.children)

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

    def set_env(self, env):
        self.env = ref(env)
        self.dispatch("set_env", env)

    def rewrite(self):
        self.dispatch("rewrite")

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

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        struct, self.name = map(str, cast(TokenList, self.tokens)[:2])

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

    def rewrite(self):
        Syntax.rewrite(self)
        new_children = []
        for child in self.children:
            if type(child) is PipelineCopy:
                target = cast(PipelineCopy, child).target
                assert(target != self.name)
                found = self.env().pipelines.get(target)
                if found:
                    new_children += found.children
            else:
                new_children.append(child)
        self.populate(new_children)


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

    def __repr__(self):
        return f'<RendererUpdate {self.resource}>'


class RendererDraw(Syntax):
    """
    A draw call.
    """
    rename = "draws"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        draw, self.name = map(str, cast(TokenList, self.tokens)[:2])

    def __repr__(self):
        return f'<RendererDraw {self.name}>'


class RendererDrawBind(Syntax):
    """
    A resource binding for a draw call.
    """
    rename = "binds"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        bind, self.binding, self.resource = map(str, cast(TokenList, self.tokens))

    def __repr__(self):
        return f'<RendererDrawBind {self.binding}, {self.resource}>'


class Program(Syntax):
    """
    This is the syntax graph root, and represents everything within your program.
    """
    rename = "programs"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        self.set_env(self)
        self.rewrite()


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


def validate(parser:Parser):
    """
    Validate the program's tokens against the grammar tree, and then return the
    abstract syntax tree.
    """

    def error(hint:str, token:Token):
        message = parser.message(hint, *token.pos(), *token.pos())
        raise GrammarError(message)

    tokens = parser.parse()
    children:List[Syntax] = []
    for token in tokens:
        if type(token) is not TokenComment:
            token = CAST(TokenList, token)
            children.append(cast(Syntax, GRAMMAR.validate(token, error)))

    return Program(None, children, GRAMMAR.constructors())
