
from .glsl_types import *
from ..syntax.grammar import PipelineInterface


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
    template = "layout(std140, binding = 「binding_point」)\nuniform 「name」\n{\n「members」\n}「instance_name」;"
    indent = ("members",)
    def __init__(self, struct: StructType, binding_point: int, block_name: str, instance_name: str = ""):
        SyntaxExpander.__init__(self)
        self.name = block_name
        self.binding_point = binding_point
        self.members = [GlslMember(*member) for member in struct.members.items()]
        self.instance_name = instance_name


class TextureInterface(SyntaxExpander):
    template = "layout(binding = 「binding_point」)\nuniform sampler「mode:str」 「name:str」;"

    def __init__(self, interface: PipelineInterface):
        SyntaxExpander.__init__(self)
        self.binding_point = interface.texture_unit
        self.mode = self.sampler_type(interface.format.target)
        self.name = interface.name

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
        elif target == "GL_TEXTURE_2D_MULTISAMPLE_ARRAY":
            return "2DMSArray"
