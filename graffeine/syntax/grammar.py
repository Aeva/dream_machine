
from weakref import ref
from ..handy import *
from .tokens import *
from .parser import Parser
from .arithmetic import fold, FoldedExpression, UnfoldedExpression
from ..expanders.glsl_types import glsl_builtins


ErrorCallback = Callable[..., None]


COMMON_VARS = \
(
    "ScreenWidth",
    "ScreenHeight",
    "ScreenScaleX",
    "ScreenScaleY",
)


class Syntax:
    """
    Base class for abstract syntax objects, to be filled out by grammar Rule
    objects.

    Subclasses must specify the "one" or "many" class variable, which graph
    parents use for placement in attribute lists or dictionaries.

    If "one" is set, there will be a one-to-one relationship between the
    child and parent.  If "many" is set, then the relationship is many-to-one.

    Subclasses of the "many" variety may specify a "primary" class variable,
    which then denotes an attribute within the subclass that should be used as
    a primary key for dictionary lookups within a graph parent.

    Syntax classes are meant to be created by Rule classes upon successful
    validaiton.
    """
    one:Optional[str] = None
    many:Optional[str] = None
    primary:Optional[str] = None

    def __init__(self, tokens:Optional[TokenList], children, child_types):
        assert((type(self.one) is str and self.many is None) or (type(self.many) is str and self.one is None))
        cast(List[Syntax], children)
        cast(List[Type[Syntax]], child_types)
        self.tokens = tokens
        self.children = children
        self.child_types = child_types
        self._keys = dedupe([cast(str, c.many or c.one) for c in child_types])
        self.env:Optional[Program] = None
        self._parent:Optional[ref] = None
        self.error_callback:Optional[ErrorCallback] = None
        for child in self.children:
            child.parent = self
        self.populate(self.children)

    @property
    def parent(self):
        assert(self._parent is not None)
        return cast(Syntax, self._parent())

    @parent.setter
    def parent(self, parent):
        assert(self._parent is None)
        self._parent = ref(parent)

    def error(self, hint:str, token:Optional[Token] = None):
        """
        This will generate a nice error message for the user w/ context and
        raise a ValidationError.

        This should only be called from the "rewrite" or "validate" methods
        from subclasses.
        """
        error_callback = cast(ErrorCallback, self.error_callback)
        error_callback(hint, token or CAST(TokenList, self.tokens))

    def populate(self, all_children):
        for match in self.child_types:
            children = [c for c in all_children if type(c) == match]
            if match.many is not None:
                if match.primary:
                    setattr(self, match.many, {getattr(c, match.primary) : c for c in children})
                else:
                    setattr(self, match.many, children)
            else:
                assert(match.one is not None)
                child = children[-1] if len(children) else None
                setattr(self, match.one, child)

    def subset(self, subset_name):
        subset = getattr(self, subset_name)
        if is_mapping(subset):
            return subset.values()
        elif is_sequence(subset):
            return subset
        elif subset is None:
            return []
        else:
            return [subset]

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
            if is_mapping(subset):
                for primary, child in subset.items():
                    msg += indent(f'"{primary}":\n{indent(child.report())}')
            elif is_sequence(subset):
                for child in subset:
                    msg += indent(child.report())
            else:
                msg += indent(child.report())
        return f'{repr(self)}\n{indent(msg)}'

    def __repr__(self):
        return f'<{type(self).__name__}>'


class ArithmeticExpression(Syntax):
    """
    This wraps the result from the function "fold" in the arithmetic module.
    """
    one = "expr"

    def __init__(self, expr:Union[FoldedExpression, UnfoldedExpression], *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        self.expr = expr

    def validate(self, expr:Optional[Any]=None):
        expr = expr or self.expr
        if type(expr) is str:
            if not expr in COMMON_VARS:
                self.error(f'Unknown variable "{expr}"', self.tokens)
        elif type(expr) is UnfoldedExpression:
            expr = cast(UnfoldedExpression, expr)
            for arg in expr.args:
                self.validate(arg)
        else:
            assert(type(expr) in (int, str))


class Struct(Syntax):
    """
    This represents a struct type definition, which may be used to generate GLSL
    structs, GLSL uniform blocks, C++ structs, and C++ side buffer upload functions.
    """
    many = "structs"
    primary = "name"
    members:dict

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
    many = "members"

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
    many = "samplers"
    primary = "name"
    filters:dict

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        sampler, self.name = map(str, cast(TokenList, self.tokens)[:2])

    @property
    def handle(self):
        return list(self.env().samplers.keys()).index(self.name)

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
    many = "filters"
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
    many = "formats"
    primary = "name"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        format, self.name, self.target, self.format, self._sampler = map(str, cast(TokenList, self.tokens))

    @property
    def sampler(self):
        return self.env().samplers.get(self._sampler)

    def validate(self):
        Syntax.validate(self)
        if self.target != "GL_TEXTURE_2D":
            self.error(f'Unsupported texture target: "{self.target}"')
        if self.format != "GL_RGBA8":
            self.error(f'Unsupported texture format: "{self.format}"')
        if self.sampler is None:
            self.error(f'Unknown sampler: "{self._sampler}"')
        if self.name in self.env().structs:
            self.error(f'There cannot be a format named "{self.name}", because there is already a struct of the same name.')

    def __repr__(self):
        return f'<Format {self.name} {self.target} {self.format} {self.sampler}>'


class Pipeline(Syntax):
    """
    This represents the pipeline state needed for a draw call.
    This specifies shaders, data interfaces, and fixed function state.
    """
    many = "pipelines"
    primary = "name"
    structs:dict
    shaders:dict
    interfaces:dict

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

    def uniforms(self) -> tuple: #Tuple[PipelineInterface, ...]:
        """
        Returns the pipeline's uniform interfaces.
        """
        return tuple([i for i in self.interfaces.values() if i.is_uniform])

    def textures(self) -> tuple: #Tuple[PipelineInterface, ...]:
        """
        Returns the pipeline's texture interfaces.
        """
        return tuple([i for i in self.interfaces.values() if i.is_texture])

    def binding_index(self, name:str) -> int:
        return [i.name for i in self.uniforms()].index(name)

    def texture_unit(self, name:str) -> int:
        return [i.name for i in self.textures()].index(name)


class PipelineShader(Syntax):
    """
    A path to a shader to be used by a pipeline.
    """
    many = "shaders"
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
    many = "structs"

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
    many = "interfaces"
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

    @property
    def format(self):
        return self.env().formats.get(self.type)

    @property
    def binding_index(self):
        assert(self.is_texture)
        return self.parent.binding_index(self.name)

    @property
    def texture_unit(self):
        assert(self.is_texture)
        return self.parent.texture_unit(self.name)

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
    many = "flags"
    primary = "flag"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        self.state, self.flag = map(str, cast(TokenList, self.tokens))

    def __repr__(self):
        return f'<PipelineFlag {self.flag} = {self.state == "enable"}>'

    def value(self):
        return self.state == "enable"


class PipelineCopy(Syntax):
    """
    This copies in all of the commands from another pipeline.  Commands are
    taken in order, and the last command of a given type is the one that is used.
    """
    many = "copies"

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
    many = "buffers"
    primary = "name"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        buffer, self.name, self.struct = map(str, cast(TokenList, self.tokens))

    @property
    def handle(self):
        return list(self.env().buffers.keys()).index(self.name)

    def validate(self):
        Syntax.validate(self)
        if self.name in self.env().samplers:
            self.error(f'Buffer cannot be named "{self.name}", because there is already a sampler of the same name.')
        if self.struct not in self.env().structs:
            self.error(f'Unknown struct: "{self.struct}"')

    def __repr__(self):
        return f'<Buffer {self.name} {self.struct}>'


class Texture(Syntax):
    """
    This corresponds to a texture object, and is used for binding and upload
    machinery.
    """
    many = "textures"
    primary = "name"
    src:Syntax

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        buffer, self.name, self._format = map(str, cast(TokenList, self.tokens[:3]))

    @property
    def format(self):
        return self.env().formats[self._format]

    @property
    def handle(self):
        return list(self.env().textures.keys()).index(self.name)

    @property
    def sampler(self):
        return self.format.sampler

    @property
    def width(self):
        prop = self.dimensions.get("width")
        return prop.value if prop is not None else None

    @property
    def height(self):
        prop = self.dimensions.get("height")
        return prop.value if prop is not None else None

    @property
    def depth(self):
        prop = self.dimensions.get("depth")
        return prop.value if prop is not None else None

    def validate(self):
        Syntax.validate(self)
        if self.name in self.env().samplers:
            self.error(f'Texture cannot be named "{self.name}", because there is already a sampler of the same name.')
        if self.name in self.env().buffers:
            self.error(f'Texture cannot be named "{self.name}", because there is already a buffer of the same name.')
        if not self.format:
            self.error(f'Unknown format: "{self.format}"')

        has_width = self.width is not None
        has_height = self.height is not None
        has_depth = self.depth is not None

        if self.format.target == "GL_TEXTURE_2D":
            if not (has_width and has_height) and not self.src:
                self.error("2D textures must either load a file or specify width and height.")
            if has_depth:
                self.error("2D textures can't have depth specified.")

        if self.format.target == "GL_TEXTURE_3D":
            if self.src:
                self.error("3D textures don't current support loading from files.")
            if not (has_width and has_height and has_depth):
                self.error("2D textures must specify width, height, and depth.")

        if self.src and (has_width or has_height or has_depth):
            self.error("Textures which define a source image can't also specify their dimensions.")

        if self.src and self.format.format != "GL_RGBA8":
            self.error("Loading textures from images is currently only supported for GL_RGBA8 textures.")

    def __repr__(self):
        return f'<Texture {self.name} {self.format}>'


class TextureSrc(Syntax):
    """
    Command for loading the image from a file.  If this is set, the dimensions
    of the image should not also be provided as they will be determined at run time.
    """
    one = "src"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        load, self.path = map(str, cast(TokenList, self.tokens))

    def validate(self):
        pass

    def __repr__(self):
        return self.path


class TextureDimension(Syntax):
    """
    Intended to be subclassed.
    """
    many = "dimensions"
    primary = "name"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        self.name = str(cast(TokenList, self.tokens)[0])

    @property
    def value(self):
        return self.expr.expr

    def __repr__(self):
        return r'<TextureDimension {self.name} : {str(self.value)}>'


class Renderer(Syntax):
    """
    This defines one of your application's renderers, which essentially is the
    specification for what is to be rendered in a given frame.  Only one
    renderer is used per frame, but the renderer can be changed between frames.
    """
    many = "renderers"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        renderer, self.name = map(str, cast(TokenList, self.tokens)[:2])

    def __repr__(self):
        return f'<Renderer {self.name}>'


class RendererUpdate(Syntax):
    """
    This specifies that a given handle should be updated with user data.
    """
    many = "updates"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        update, self.resource = map(str, cast(TokenList, self.tokens))

    def validate(self):
        Syntax.validate(self)
        if self.resource not in self.env().textures and self.resource not in self.env().buffers:
            self.error(f'Unknown texture or buffer: "{self.resource}"')

    @property
    def texture(self):
        return self.env().textures.get(self.resource)

    @property
    def buffer(self):
        return self.env().buffers.get(self.resource)

    def __repr__(self):
        return f'<RendererUpdate {self.resource}>'


class RendererDraw(Syntax):
    """
    A draw call.
    """
    many = "draws"
    binds:tuple #Tuple[RendererDrawBind]

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
            if bind.name not in pipeline.bindings:
                bind.error(f'Binding "{bind.name}" is not an interface in this draw\'s pipeline.  See pipeline "{self.pipeline}."')

            # check the binding against the referenced pipeline
            interface:PipelineInterface = pipeline.interfaces[bind.name]
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
                    if bind.texture.format.name != interface.type:
                        # TODO: really we just care if the target is compatible, and maybe if the channels are the same
                        bind.error(f'Texture is format "{texture.format}", but the interface expects "{interface.type}"')
                else:
                    assert(bind.is_sampler)

    def __repr__(self):
        return f'<RendererDraw {self.pipeline}>'

    def buffer_bindings(self) -> tuple: #Tuple[RendererDrawBind, ...]:
        """
        Returns the draw's uniform bindings.
        """
        return tuple([i for i in self.binds if i.is_buffer])

    def texture_bindings(self) -> tuple: #Tuple[RendererDrawBind, ...]:
        """
        Returns the draw's texture bindings.
        """
        return tuple([i for i in self.binds if i.is_texture])

    def sampler_bindings(self) -> tuple: #Tuple[RendererDrawBind, ...]:
        """
        Returns the draw's sampler bindings.
        """
        return tuple([i for i in self.binds if i.is_sampler])


class RendererDrawBind(Syntax):
    """
    A resource binding for a draw call.
    """
    many = "binds"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        bind, self.name, self.resource = map(str, cast(TokenList, self.tokens))
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

    @property
    def interface(self):
        pipeline = self.env().pipelines[self.parent.pipeline]
        return pipeline.interfaces[self.name]

    @property
    def texture(self):
        return self.env().textures.get(self.resource)

    @property
    def sampler(self):
        if self.is_texture:
            return self.texture.sampler
        else:
            return self.env().samplers.get(self.resource)

    @property
    def buffer(self):
        return self.env().buffers.get(self.resource)

    def __repr__(self):
        return f'<RendererDrawBind {self.name}, {self.resource}>'


class Program(Syntax):
    """
    This is the syntax graph root, and represents everything within your program.
    """
    many = "programs"
    structs:dict
    buffers:dict
    samplers:dict
    textures:dict
    pipelines:dict
    renderers:dict

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


class ArithmeticRule(Rule):
    """
    This will attempt to match a valid arithmetic expresison.
    """

    def constructors(self) -> List[type]:
        return [ArithmeticExpression]

    def validate(self, token:Token, error:ErrorCallback) -> Optional[Syntax]:
        expr:Union[FoldedExpression, UnfoldedExpression] = fold(token, error)
        return ArithmeticExpression(expr, token, [], [])


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
                child_types += rule.constructors()
        if self.splat:
            remainder = cast(Tuple[Token], token_list[len(self.rules):])
            child_types += self.splat.constructors()
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
