
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


from .glsl_types import *


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
