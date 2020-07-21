
from .glsl_types import *
from .common import SyntaxExpander
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
        self.handle = input.buffer.handle


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
