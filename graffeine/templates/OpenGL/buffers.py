
from ..import *


class BufferHandle(SyntaxExpander):
    template = "GLuint BufferHandles[「count」] = { 0 };"


class CreateBuffers(SyntaxExpander):
    template = "glCreateBuffers(「count」, &BufferHandles[「handle」]);"


class DeleteBuffers(SyntaxExpander):
    template = "glCreateBuffers(「count」, &BufferHandles[「handle」]);"


class BufferStorage(SyntaxExpander):
    template = "glNamedBufferStorage(BufferHandles[「handle」], 「bytes」, nullptr, GL_DYNAMIC_STORAGE_BIT | GL_MAP_WRITE_BIT);"


class ResizeBuffer(SyntaxExpander):
    template = "「wrapped」"
    def __init__(self, handle: int, bytes: int) -> None:
        self.wrapped = [
            DeleteBuffers(handle=handle, count=1),
            CreateBuffers(handle=handle, count=1), 
            BufferStorage(handle=handle, bytes=bytes)
        ]
