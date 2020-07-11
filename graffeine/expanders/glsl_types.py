
from typing import *
from .common import SyntaxExpander, align


class GlslType:
    def __init__(self, name: str, alignment: int, words: int) -> None:
        self.name = name
        self.alignment = alignment
        self.words = words
        self.array_size = 0
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} \"{self.name}\" {self.alignment} {self.words}>"
    def __eq__(self, other):
        return (self.name, self.alignment, self.words) == (other.name, other.alignment, other.words)
    def __hash__(self):
        return (self.name, self.alignment, self.words)
    @property
    def bytes(self):
        return self.words * 4


class ScalarType(GlslType):
    def __init__(self, name: str) -> None:
        GlslType.__init__(self, name, 1, 1)


class VectorType(GlslType):
    def __init__(self, name: str, size: int) -> None:
        assert(size > 1)
        assert(size <= 4)
        GlslType.__init__(self, f"{name}{size}", align(size, 2), size)


class ArrayType(GlslType):
    def __init__(self, base: GlslType, size: int) -> None:
        self.array_size = size
        self.item_type = base
        self.item_type.words = align(base.words, 4)
        self.item_type.alignment = base.alignment
        GlslType.__init__(self, f"{base.name}", self.item_type.alignment, self.item_type.words * size)


class MatrixType(ArrayType):
    def __init__(self, name: str, size: int) -> None:
        assert(size > 1)
        assert(size <= 4)
        ArrayType.__init__(self, VectorType(f"vec", size), size)
        self.name = f"{name}{size}"


class StructType(GlslType):
    def __init__(self, struct_name: str, **members):
        assert(len(members) > 0)
        self.members:Dict[str, GlslType] = members
        alignment = 0
        for name, member in members.items():
            alignment = max(alignment, member.alignment)
        alignment = align(alignment, 4)
        words = 0
        for member in members.values():
            words = align(words, member.alignment) + member.words
        words = align(words, 4)
        GlslType.__init__(self, struct_name, alignment, words)
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} \"{self.name}\" {self.alignment} {self.words} {self.members}>"


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


class RealignCopy(SyntaxExpander):
    template = "Reflow<「upload_type」>(Mapped, 「offset」, Data.「field」);"

    def __init__(self, upload_type: str, offset: int, field: str) -> None:
        SyntaxExpander.__init__(self)
        if upload_type in ["int", "bool"]:
            upload_type = f"_{upload_type}"
        while len(upload_type) < 5:
            upload_type = f" {upload_type}"
        self.upload_type = upload_type
        self.offset = offset
        self.field = field


def solve_array_reflow(array, offset: int, base: str) -> list:
    assert(type(array) in [ArrayType, MatrixType])
    copies = []
    if type(array.item_type) in [ScalarType, VectorType]:
        for i in range(array.array_size):
            field = f"{base}[{i}]"
            copies.append(RealignCopy(array.item_type.name, offset, field))
            offset += array.item_type.words
    elif type(array.item_type) in [MatrixType, ArrayType]:
        for i in range(array.array_size):
            field = f"{base}[{i}]"
            copies += solve_array_reflow(array.item_type, offset, field)
            offset += array.item_type.words
    elif type(array.item_type) is StructType:
        for i in range(array.array_size):
            field = f"{base}[{i}]."
            copies += solve_struct_reflow(array.item_type, offset, field)
            offset += array.item_type.words
    return copies


def solve_struct_reflow(struct, offset: int = 0, base: str = "") -> list:
    assert(type(struct) is StructType)
    copies = []
    for member_name, member_type in struct.members.items():
        offset = align(offset, member_type.alignment)
        if type(member_type) in [ScalarType, VectorType]:
            field = f"{base}{member_name}"
            copies.append(RealignCopy(member_type.name, offset, field))
            offset += member_type.words
        elif type(member_type) in [MatrixType, ArrayType]:
            field = f"{base}{member_name}"
            copies += solve_array_reflow(member_type, offset, field)
            offset = align(offset + member_type.words, member_type.alignment)
        elif type(member_type) is StructType:
            field = f"{base}{member_name}."
            copies += solve_struct_reflow(member_type, offset, field)
            offset = align(offset + member_type.words, member_type.alignment)
    return copies


class BufferUpload(SyntaxExpander):
    template = """
void 「struct_name」 (GLuint Handle, Glsl::「struct_name」& Data)
{
	std::int32_t* Mapped = (std::int32_t*)glMapNamedBufferRange(Handle, 0, 「bytes」, GL_MAP_WRITE_BIT | GL_MAP_INVALIDATE_BUFFER_BIT);
	if (Mapped == nullptr)
	{
		std::cout << "Fatal error in function \\"Upload::「struct_name」\\": glMapNamedBufferRange returned nullptr.\\n";
		HaltAndCatchFire();
	}
「reflow」
	glUnmapNamedBuffer(Handle);
}
""".strip()
    indent = ("reflow",)
    def __init__(self, struct: StructType):
        SyntaxExpander.__init__(self)
        self.struct_name = struct.name
        self.bytes = struct.words * 4
        self.reflow = solve_struct_reflow(struct)


glsl_builtins = {
    "bool" : ScalarType("bool"),
    "int" : ScalarType("int"),
    "uint" : ScalarType("uint"),
    "float" : ScalarType("float"),
    "bvec2" : VectorType("bvec", 2),
    "bvec3" : VectorType("bvec", 3),
    "bvec4" : VectorType("bvec", 4),
    "ivec2" : VectorType("ivec", 2),
    "ivec3" : VectorType("ivec", 3),
    "ivec4" : VectorType("ivec", 4),
    "uvec2" : VectorType("uvec", 2),
    "uvec3" : VectorType("uvec", 3),
    "uvec4" : VectorType("uvec", 4),
    "vec2" : VectorType("vec", 2),
    "vec3" : VectorType("vec", 3),
    "vec4" : VectorType("vec", 4),
    "mat2" : MatrixType("mat", 2),
    "mat3" : MatrixType("mat", 3),
    "mat4" : MatrixType("mat", 4),
}
