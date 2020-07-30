
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
        words = align(base.words, 4)
        GlslType.__init__(self, f"{base.name}", base.alignment, words * size)
        self.array_size = size
        self.item_type = base
        self.item_type.words = words
        self.item_type.alignment = base.alignment


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
