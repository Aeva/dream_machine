
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
from ..expanders import SyntaxExpander
from ..handy import CAST
from ..syntax.grammar import Buffer, PipelineInput, Program


class BufferHandles(SyntaxExpander):
    template = "GLuint BufferHandles[「count」] = { 0 };"


class CreateBuffers(SyntaxExpander):
    template = "glCreateBuffers(「count」, &BufferHandles[「start」]);"

    def __init__(self, count:int, start:int=0):
        SyntaxExpander.__init__(self, count=count, start=start)


class DeleteBuffers(SyntaxExpander):
    template = "glDeleteBuffers(「count」, &BufferHandles[「start」]);"


class BufferStorage(SyntaxExpander):
    template = "glNamedBufferStorage(BufferHandles[「handle」], 「bytes」, nullptr, GL_DYNAMIC_STORAGE_BIT | GL_MAP_WRITE_BIT);"


class ResizeBuffer(SyntaxExpander):
    template = "「wrapped」"
    def __init__(self, handle: int, bytes: int) -> None:
        self.wrapped = [
            DeleteBuffers(start=handle, count=1),
            CreateBuffers(start=handle, count=1), 
            BufferStorage(handle=handle, bytes=bytes)
        ]


class BindUniformBuffer(SyntaxExpander):
    template = "glBindBufferBase(GL_UNIFORM_BUFFER, 「binding_index:int」, BufferHandles[「handle:int」]);"

    def __init__(self, input:PipelineInput):
        SyntaxExpander.__init__(self)
        self.binding_index = input.uniform_index
        self.handle = CAST(Buffer, input.buffer).handle


class BufferSetup(SyntaxExpander):
    template = """
{
	// buffer "「name:str」"
	glNamedBufferStorage(BufferHandles[「handle:int」], 「bytes:int」, nullptr, GL_DYNAMIC_STORAGE_BIT | GL_MAP_WRITE_BIT);
	glObjectLabel(GL_BUFFER, BufferHandles[「handle:int」], -1, \"「name:str」\");
}
""".strip()
    def __init__(self, buffer:Buffer, struct:StructType):
        SyntaxExpander.__init__(self)
        self.name = buffer.name
        self.handle = buffer.handle
        self.bytes = struct.bytes


class SetupBuffers(SyntaxExpander):
    template = """
{
「wrapped」
}
""".strip()
    indent = ("wrapped",)

    def __init__(self, env:Program, solved_structs:Dict[str,StructType]):
        SyntaxExpander.__init__(self)
        self.wrapped:List[SyntaxExpander] = [CreateBuffers(len(env.buffers))]
        for buffer in env.buffers.values():
            struct = solved_structs[buffer.struct]
            self.wrapped.append(BufferSetup(buffer, struct))
