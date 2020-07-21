
from .glsl_types import *
from ..syntax.grammar import PipelineInput, PipelineOutput


class GlslMember(SyntaxExpander):
    template = "「type」 「name」「array」;"
    def __init__(self, member_name: str, member_type: GlslType):
        SyntaxExpander.__init__(self)
        self.type = member_type.name
        self.name = member_name
        self.array = ""
        if (type(member_type) is ArrayType):
            self.array = f"[{member_type.array_size}]"


class GlslStruct(SyntaxExpander):
    template = "struct 「name」\n{\n「members」\n};"
    indent = ("members",)
    def __init__(self, struct: StructType):
        SyntaxExpander.__init__(self)
        self.name = struct.name
        self.members = [GlslMember(*member) for member in struct.members.items()]


class UniformInterface(SyntaxExpander):
    template = "layout(std140, binding = 「binding_point」)\nuniform 「block_name」\n{\n「members」\n}「instance_name」;"
    indent = ("members",)
    def __init__(self, struct: StructType, input: PipelineInput):
        SyntaxExpander.__init__(self)
        self.block_name = input.binding_name
        self.binding_point = input.uniform_index
        self.members = [GlslMember(*member) for member in struct.members.items()]
        self.instance_name = ""


class TextureInterface(SyntaxExpander):
    template = "layout(binding = 「binding_point」)\nuniform sampler「mode:str」 「name:str」;"

    def __init__(self, input: PipelineInput):
        SyntaxExpander.__init__(self)
        self.binding_point = input.texture_index
        self.mode = self.sampler_type(input.format.target)
        self.name = input.binding_name

    def sampler_type(self, target:str) -> str:
        if target == "GL_TEXTURE_1D":
            return "1D"
        elif target == "GL_TEXTURE_2D":
            return "2D"
        elif target == "GL_TEXTURE_3D":
            return "3D"
        elif target == "GL_TEXTURE_RECTANGLE":
            return "2DRect"
        elif target == "GL_TEXTURE_1D_ARRAY":
            return "1DArray"
        elif target == "GL_TEXTURE_2D_ARRAY":
            return "2DArray"
        elif target == "GL_TEXTURE_CUBE_MAP":
            return "Cube"
        elif target == "GL_TEXTURE_CUBE_MAP_ARRAY":
            return "CubeArray"
        elif target == "GL_TEXTURE_BUFFER":
            return "Buffer"
        elif target == "GL_TEXTURE_2D_MULTISAMPLE":
            return "2DMS"
        else:
            assert(target == "GL_TEXTURE_2D_MULTISAMPLE_ARRAY")
            return "2DMSArray"


class TargetInterface(SyntaxExpander):
    template = "layout(location = 「index:int」)\n out 「type:str」 「name:str」;"

    def __init__(self, output: Optional[PipelineOutput]):
        SyntaxExpander.__init__(self)
        if output is not None:
            self.index = output.color_index
            self.name = output.texture.name
            self.type = "vec4"
        else:
            self.index = 0
            self.name = "OutColor"
            self.type = "vec4"
