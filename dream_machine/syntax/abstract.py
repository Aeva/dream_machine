
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


from __future__ import annotations
from math import *
from copy import copy
from weakref import ref, ReferenceType
from ..handy import *
from .tokens import *
from .parser import Parser
from .constants import *
from .arithmetic import fold, FoldedExpression, UnfoldedExpression
from ..opengl.glsl_types import glsl_builtins


ErrorCallback = Callable[..., None]
ExpressionTree = Union[FoldedExpression, UnfoldedExpression]


COMMON_VARS = \
(
    "ScreenWidth",
    "ScreenHeight",
    "ScreenScaleX",
    "ScreenScaleY",
)


SCALAR_CTYPE_NAMES = \
(
    "float",
    "double",
    "int",
    "bool",
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

    def __init__(self, tokens:Optional[TokenList], children:List[Syntax], child_types:List[Type[Syntax]], extra_types:Optional[List[Type[Syntax]]] = None):
        assert((type(self.one) is str and self.many is None) or (type(self.many) is str and self.one is None))
        self.tokens = tokens
        self.children = children
        self.child_types = child_types
        if extra_types:
            self.child_types += extra_types
        self._keys = dedupe([cast(str, c.many or c.one) for c in child_types])
        self._env:Optional[ReferenceType] = None
        self._parent:Optional[ReferenceType] = None
        self.error_callback:Optional[ErrorCallback] = None
        for child in self.children:
            child.parent = self
        self.populate(self.children)

    @property
    def env(self) -> Program:
        reference = cast(ReferenceType, self._env)
        return CAST(Program, reference())

    @property
    def parent(self) -> Syntax:
        assert(self._parent is not None)
        return cast(Syntax, self._parent())

    @parent.setter
    def parent(self, parent:Syntax):
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

    def populate(self, all_children:List[Syntax]):
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

    def append_child(self, new_child:Syntax):
        """
        Add a new child to this node and match dicts/lists.
        """
        for match in self.child_types:
            if type(new_child) == match:
                assert(match.many is not None)
                group = getattr(self, match.many)
                if match.primary:
                    cast(dict, group)
                    key = getattr(new_child, match.primary)
                    assert(key not in group)
                    group[key] = new_child
                else:
                    cast(list, group)
                    group.append(new_child)
                self.children.append(new_child)

    def subset(self, subset_name:str) -> Union[List[Syntax], Dict[str,Syntax], Syntax]:
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
        self._env = ref(env)
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

    def __init__(self, expr:ExpressionTree, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        self.expr = expr

    def validate(self, expr:Optional[Any]=None):
        expr = expr or self.expr
        if type(expr) is str:
            if not expr in COMMON_VARS and not expr in self.env.user_vars:
                self.error(f'Unknown variable "{expr}"', self.tokens)
        elif type(expr) is UnfoldedExpression:
            expr = cast(UnfoldedExpression, expr)
            for arg in expr.args:
                self.validate(arg)
        else:
            assert(type(expr) in (int, float))


class UserVar(Syntax):
    """
    This represents a user-defined variable, which may be used in expressions, and
    may be changed by user code at run time.
    """
    many = "user_vars"
    primary = "name"
    expr:ArithmeticExpression

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        uservar, self.ctype, self.name = map(str, cast(TokenList, self.tokens[:3]))

    @property
    def value(self) -> ExpressionTree:
        return self.expr.expr

    def validate(self):
        if self.ctype not in SCALAR_CTYPE_NAMES:
            self.error(f'Invalid scalar ctype: "{self.ctype}"')


class Struct(Syntax):
    """
    This represents a struct type definition, which may be used to generate GLSL
    structs, GLSL uniform blocks, C++ structs, and C++ side buffer upload functions.
    """
    many = "structs"
    primary = "name"
    members:List[StructMember]

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
            if member.type in self.env.structs and member.type not in self.referenced:
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
        token_list = CAST(TokenList, self.tokens)
        self.name = str(token_list[0])
        if str(token_list[1]) == "array":
            self.array = CAST(TokenNumber, token_list[2])
            self.type = str(token_list[3])
        else:
            self.array = None
            self.type = str(token_list[1])

    def validate(self):
        Syntax.validate(self)
        if self.type not in glsl_builtins and self.type not in self.env.structs:
            self.error(f'Undefined type name: "{self.type}"')
        if self.array is not None:
            number = CAST(TokenNumber, self.array)
            if number.value < 1:
                self.error("Array size can't be less than 1", number)
            if number.value != floor(number.value):
                pass

    def __repr__(self):
        return f'<StructMember {self.name} {self.type}>'


class Sampler(Syntax):
    """
    This describes a sampler object.  There will be one sampler created for each
    instance of this class.
    """
    many = "samplers"
    primary = "name"
    filters:Dict[str,SamplerFilter]

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        sampler, self.name = map(str, cast(TokenList, self.tokens)[:2])

    @property
    def handle(self) -> int:
        return list(self.env.samplers.keys()).index(self.name)

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
        self.name, self.value_str = map(str, cast(TokenList, self.tokens))

    @property
    def value(self) -> SamplerFilterType:
        try:
            return SamplerFilterType[self.value_str]
        except:
            self.error(f'Unsupported sampler filter value: "{self.value_str}"')

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
        ignore, self.name, self.target_str, self.format_str, self._sampler = map(str, cast(TokenList, self.tokens))

    @property
    def sampler(self) -> Sampler:
        return CAST(Sampler, self.env.samplers.get(self._sampler))

    @property
    def target(self) -> TextureType:
        try:
            return TextureType[self.target_str]
        except:
            self.error(f'Unknown texture type: "{self.target_str}"')

    @property
    def format(self) -> TextureFormats:
        try:
            return TextureFormats[self.format_str]
        except:
            self.error(f'Unknown texture format: "{self.format_str}"')

    def validate(self):
        Syntax.validate(self)
        if self.sampler is None:
            self.error(f'Unknown sampler: "{self._sampler}"')
        if self.name in self.env.structs:
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
    structs:List[PipelineUse]
    shaders:Dict[str,PipelineShader]
    inputs:List[PipelineInput]
    outputs:List[PipelineOutput]
    sideputs:List[PipelineSideput]
    flags:Dict[str,PipelineFlag]

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        pipeline, self.name = map(str, cast(TokenList, self.tokens)[:2])
        self.requires_flip:List[Texture] = []

    def rewrite(self):
        Syntax.rewrite(self)
        new_children = []
        for child in self.children:
            if type(child) is PipelineCopy:
                target = cast(PipelineCopy, child).target
                if target == self.name:
                    child.error("A pipeline can't copy itself!")
                found = self.env.pipelines.get(target)
                if found:
                    new_children += found.children
            else:
                new_children.append(child)
        self.populate(new_children)

        # create shadow targets where needed
        input_textures = (i.texture for i in self.textures if i.texture)
        input_handles = [t.handle for t in input_textures]
        shadowed_targets = tuple([o for o in self.outputs if o.handle in input_handles])
        for target in shadowed_targets:
            self.requires_flip.append(target.texture)
            target.texture.create_shadow_target()

    def validate(self):
        Syntax.validate(self)
        if "cs" in self.shaders:
            if len(self.shaders.keys()) > 1:
                self.error("Compute pipelines can't use non-compute shaders.")
            if len(self.outputs) > 0:
                self.error("Compute pipelines can't output to render targets.")

        # Note: API backends must perform their own validation for raster pipeline configurations.

        depth_targets = [i for i in self.outputs if i.is_depth]
        if len(depth_targets) > 1:
            self.error(f'Pipeline "{self.name}" has {len(depth_targets)} depth outputs, but pipelines can have only one depth output.')

    @property
    def index(self) -> int:
        return list(self.env.pipelines.values()).index(self)

    @property
    def uniforms(self) -> Tuple[PipelineInput, ...]:
        """
        Returns the pipeline's uniform inputs.
        """
        return tuple([i for i in self.inputs if i.is_uniform])

    @property
    def textures(self) -> Tuple[PipelineInput, ...]:
        """
        Returns the pipeline's texture inputs.
        """
        return tuple([i for i in self.inputs if i.is_texture])

    @property
    def all_target_textures(self) -> List[Texture]:
        explicit_textures = [o.texture for o in self.outputs]
        implicit_textures = [t.shadow_texture for t in explicit_textures if t.shadow_texture]
        return explicit_textures + implicit_textures

    @property
    def color_targets(self) -> Tuple[PipelineOutput, ...]:
        return tuple([i for i in self.outputs if i.is_color])

    @property
    def depth_target(self) -> Optional[PipelineOutput]:
        targets = [i for i in self.outputs if i.is_depth]
        if len(targets) == 1:
            return targets[0]
        else:
            return None

    @property
    def uses_backbuffer(self) -> bool:
        return self.depth_target is None and len(self.color_targets) == 0

    @property
    def any_output_double_buffered(self) -> bool:
        for output in self.outputs:
            if output.texture.shadow_texture:
                return True
        return False

    def compatible_with(self, other) -> bool:
        """
        Compare this pipeline object with another, and return True if the two use
        the same output buffers in the same order.
        """
        if len(self.outputs) == len(other.outputs):
            for lhs, rhs in zip(self.outputs, other.outputs):
                if lhs.resource_name != rhs.resource_name:
                    return False
            return True
        else:
            return False

    def __repr__(self):
        return f'<Pipeline {self.name}>'


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
        if self.struct not in self.env.structs:
            self.error(f'Unknown struct "{self.struct}"')

    def __repr__(self):
        return f'<PipelineUse {self.struct}>'


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
        if self.target not in self.env.pipelines:
            self.error(f'Unknown pipeline copy target: "{self.target}"')

    def __repr__(self):
        return f'<PipelineCopy {self.target}>'


class PipelineInput(Syntax):
    """
    A buffer or texture input for a pipeline.
    """
    many = "inputs"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        cmd, self.resource_name = tuple(map(str, cast(TokenList, self.tokens[:2])))

    @property
    def binding_name(self) -> str:
        return self.resource_name

    @property
    def is_texture(self) -> bool:
        return self.resource_name in self.env.textures

    @property
    def is_uniform(self) -> bool:
        return self.resource_name in self.env.buffers

    @property
    def texture(self) -> Optional[Texture]:
        return self.env.textures.get(self.resource_name)

    @property
    def format(self) -> Format:
        return CAST(Texture, self.texture).format

    @property
    def buffer(self) -> Optional[Buffer]:
        return self.env.buffers.get(self.resource_name)

    @property
    def struct(self) -> str:
        return CAST(Buffer, self.buffer).struct

    @property
    def uniform_index(self) -> int:
        assert(self.is_uniform)
        return cast(Pipeline, self.parent).uniforms.index(self)

    @property
    def texture_index(self) -> int:
        assert(self.is_texture)
        return cast(Pipeline, self.parent).textures.index(self)

    def validate(self):
        Syntax.validate(self)
        if not (self.is_texture or self.is_uniform):
            self.error(f'Unable to determine input type for resource "{self.resource_name}" on pipeline "{self.parent.name}".')
        # Strictly speaking it should be an error to be both, but it is more
        # useful to raise the error for buffers and structs of the same name.

    def __repr__(self):
        mode = "texture" if self.is_texture else "uniform"
        return f'<PipelineInput {mode} {self.resource_name}>'


class PipelineOutput(Syntax):
    """
    A render target output for a pipeline.
    """
    many = "outputs"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        cmd, self.resource_name = tuple(map(str, cast(TokenList, self.tokens[:2])))

    @property
    def texture(self) -> Texture:
        return self.env.textures[self.resource_name]

    @property
    def requires_flip(self) -> bool:
        return self.texture.shadow_texture != None

    @property
    def handle(self) -> int:
        return self.texture.handle

    @property
    def is_color(self) -> bool:
        return self.texture.format.format in COLOR_TEXTURE_FORMATS

    @property
    def is_depth(self) -> bool:
        return self.texture.format.format in DEPTH_TEXTURE_FORMATS

    @property
    def color_index(self) -> int:
        assert(self.is_color)
        return cast(Pipeline, self.parent).color_targets.index(self)

    def validate(self):
        Syntax.validate(self)
        if self.texture is None:
            self.error(f'Can\'t find resource "{self.resource_name}".')
        if not self.is_color and not self.is_depth:
            self.error(f'Output texture "{self.resource_name}" does not have a format which is valid for use as a render target.')
        for texture in self.parent.textures:
            if texture == self.texture:
                self.error(f'Texture "{self.resource_name}" cannot be used as both an input and output to pipeline "{self.parent.name}".')

    def __repr__(self):
        mode = "color" if self.is_color else "depth"
        return f'<PipelineOutput {mode} {self.resource_name}>'


class PipelineSideput(Syntax):
    """
    A UAV (D3D) or Image (OpenGL).
    """

    many = "sideputs"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        cmd, self.resource_name = tuple(map(str, cast(TokenList, self.tokens[:2])))

    @property
    def texture(self) -> Optional[Texture]:
        return self.env.textures.get(self.resource_name)

    @property
    def format(self) -> Format:
        return CAST(Texture, self.texture).format

    @property
    def binding_index(self) -> int:
        return cast(Pipeline, self.parent).sideputs.index(self)

    def validate(self):
        Syntax.validate(self)
        if self.texture is None:
            self.error(f'Can\'t find resource "{self.resource_name}".')

    def __repr__(self):
        return f'<PipelineSideput {self.resource_name}>'


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
    def handle(self) -> int:
        return list(self.env.buffers.keys()).index(self.name)

    def validate(self):
        Syntax.validate(self)
        if self.name in self.env.samplers:
            self.error(f'Buffer cannot be named "{self.name}", because there is already a sampler of the same name.')
        if self.struct not in self.env.structs:
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
    src:TextureSrc
    clear:TextureClearColor
    dimensions:Dict[str,TextureDimension]

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        buffer, self.name, self._format = map(str, cast(TokenList, self.tokens[:3]))
        self.shadow_texture:Optional[Texture] = None
        self.copies_from:Optional[str] = None

    def new_shadow_name(self):
        assert(self.shadow_texture != None)
        assert(self.copies_from == None)
        new_name = f"{self.name}Target"
        attempts = 1
        while new_name in self.env.textures:
            new_name = f"{self.name}Target{attempts}"
            attempts += 1
        return new_name

    def create_shadow_target(self) -> Texture:
        assert(self.copies_from == None)
        if self.shadow_texture == None:
            self.shadow_texture = copy(self)
            self.shadow_texture.copies_from = self.name
            self.shadow_texture.name = self.new_shadow_name()
            self.env.append_child(self.shadow_texture)
        return self.shadow_texture

    @property
    def format(self) -> Format:
        return self.env.formats[self._format]

    @property
    def handle(self) -> int:
        return list(self.env.textures.keys()).index(self.name)

    @property
    def sampler(self) -> Sampler:
        return self.format.sampler

    @property
    def width(self) -> Optional[ExpressionTree]:
        prop = self.dimensions.get("width")
        return prop.value if prop is not None else None

    @property
    def height(self) -> Optional[ExpressionTree]:
        prop = self.dimensions.get("height")
        return prop.value if prop is not None else None

    @property
    def depth(self) -> Optional[ExpressionTree]:
        prop = self.dimensions.get("depth")
        return prop.value if prop is not None else None

    def validate(self):
        Syntax.validate(self)
        if self.name in self.env.samplers:
            self.error(f'Texture cannot be named "{self.name}", because there is already a sampler of the same name.')
        if self.name in self.env.buffers:
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

        if self.src and self.format.format != TextureFormats.RGBA_8_UNORM:
            self.error("Loading textures from images is currently only supported for RGBA_8_UNORM textures.")

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


class TextureClearColor(Syntax):
    """
    Optional clear color.
    """
    one = "clear"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        self.channels = [t.value for t in cast(TokenList, self.tokens[1:5])]


class TextureDimension(Syntax):
    """
    Intended to be subclassed.
    """
    many = "dimensions"
    primary = "name"
    expr:ArithmeticExpression

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        self.name = str(cast(TokenList, self.tokens)[0])

    @property
    def value(self) -> ExpressionTree:
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
        Syntax.__init__(self, *args, extra_types = [RendererTextureSwap, RendererRegenFrameBuffer], **kargs)
        renderer, self.name = map(str, cast(TokenList, self.tokens)[:2])

    def solve_implicit_steps(self):
        events = []
        for event in self.children:
            if type(event) == RendererDraw:
                # update the frame buffer if the event writes to a double buffered texture
                event = cast(RendererDraw, event)
                if event.pipeline.any_output_double_buffered:
                    events.append(RendererRegenFrameBuffer(event.pipeline))

                # process the event
                events.append(event)

                # flip double buffered textures that were used as both inputs and outputs in the event
                double_buffered = event.pipeline.requires_flip
                if double_buffered:
                    for texture in double_buffered:
                        events.append(RendererTextureSwap(texture))
            else:
                events.append(event)
        self.populate(events)
        self.children = events

    @property
    def next(self) -> Optional[str]:
        if self.next_renderer:
            return self.next_renderer.name
        else:
            return None

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
        if self.resource not in self.env.textures and self.resource not in self.env.buffers:
            self.error(f'Unknown texture or buffer: "{self.resource}"')

    @property
    def texture(self) -> Optional[Texture]:
        return self.env.textures.get(self.resource)

    @property
    def buffer(self) -> Optional[Buffer]:
        return self.env.buffers.get(self.resource)

    def __repr__(self):
        return f'<RendererUpdate {self.resource}>'


class RendererDraw(Syntax):
    """
    A draw call.
    """
    many = "draws"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        draw, self.pipeline_name = map(str, cast(TokenList, self.tokens)[:2])
        self.vertices = self.tokens[2].value

    def validate(self):
        Syntax.validate(self)

        # verify that the referenced pipeline exists
        if self.pipeline_name not in self.env.pipelines:
            self.error(f'Unknown pipeline: "{self.pipeline}"')

    @property
    def pipeline(self) -> Pipeline:
        return self.env.pipelines[self.pipeline_name]

    def __repr__(self):
        return f'<RendererDraw {self.pipeline_name}>'


class RendererTextureSwap(Syntax):
    """
    Represents when the texture handles for a double buffered texture should be swapped.
    This is not controlled directly by the user, but rather is populated automatically.
    """
    many = "texture_swaps"

    def __init__(self, texture:Texture):
        Syntax.__init__(self, None, [], [])
        self.texture = texture


class RendererRegenFrameBuffer(Syntax):
    """
    Represent when a framebuffer or equivalent construction needs to be recreated.
    Might only be applicable to the OpenGL and WebGL backends.
    This is not controlled directly by the user, but rather is populated automatically.
    """
    many = "regen_framebuffers"

    def __init__(self, pipeline:Pipeline):
        Syntax.__init__(self, None, [], [])
        self.pipeline = pipeline


class RendererNext(Syntax):
    """
    A command to switch to a different renderer after the current one finishes.
    """
    one = "next_renderer"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        fnord, self.name = map(str, cast(TokenList, self.tokens)[:2])

    def validate(self):
        Syntax.validate(self)

        # verify that such a renderer exists
        if len([r for r in self.env.renderers if r.name == self.name]) == 0:
            self.error(f'Unknown renderer: "{self.name}"')


class RendererDispatch(Syntax):
    """
    """
    many = "dispatches"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        draw, self.pipeline_name = map(str, cast(TokenList, self.tokens)[:2])
        self.size = [t.value for t in cast(TokenList, self.tokens[2:5])]

    def validate(self):
        Syntax.validate(self)

    @property
    def pipeline(self) -> Pipeline:
        return self.env.pipelines[self.pipeline_name]

    def __repr__(self):
        return f'<RendererDispatch {self.pipeline_name}>'


class Backend(Syntax):
    """
    The rendering API to generate code for.
    """
    one = "backend"

    def __init__(self, *args, **kargs):
        Syntax.__init__(self, *args, **kargs)
        ignore, name = map(str, cast(TokenList, self.tokens)[:2])
        self.api = getattr(BackendAPI, name, BackendAPI.INVALID)

    def validate(self):
        Syntax.validate(self)
        if self.api == BackendAPI.INVALID:
            self.error("Invalid backend API")


class Program(Syntax):
    """
    This is the syntax graph root, and represents everything within your program.
    """
    many = "programs"
    backend:Backend
    user_vars:Dict[str,UserVar]
    structs:Dict[str,Struct]
    buffers:Dict[str,Buffer]
    formats:Dict[str,Format]
    samplers:Dict[str,Sampler]
    textures:Dict[str,Texture]
    pipelines:Dict[str,Pipeline]
    renderers:List[Renderer]

    @property
    def all_target_textures(self) -> List[Texture]:
        """
        Returns a list of all textures which may be used as render targets.
        """
        pipelines = (p for p in self.pipelines.values() if not p.uses_backbuffer)
        texture_names = sorted(set([t.name for p in pipelines for t in p.all_target_textures]))
        return [self.textures[t] for t in texture_names]

    def __init__(self, error_handler:ErrorCallback, *args, **kargs):
        Syntax.__init__(self, None, *args, **kargs)
        self.set_env(self, error_handler)
        self.rewrite()
        self.validate()
        for renderer in self.renderers:
            renderer.solve_implicit_steps()
