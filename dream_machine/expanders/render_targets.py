
from .textures import *
from ..syntax.grammar import PipelineAttachments


class FrameBufferHandles(SyntaxExpander):
    template = "GLuint FrameBufferHandles[「count」] = { 0 };"


class BindFrameBuffer(SyntaxExpander):
    template = "glBindFramebuffer(GL_FRAMEBUFFER, FrameBufferHandles[「handle:int」]);"

    def __init__(self, attachments:PipelineAttachments):
        SyntaxExpander.__init__(self, attachments.handle)


class BindBackBuffer(SyntaxExpander):
    template = "glBindFramebuffer(GL_FRAMEBUFFER, 0);"


class FrameBufferAttachment(SyntaxExpander):
    template = "glNamedFramebufferTexture(FrameBufferHandles[「rt_handle:int」], 「attachment:str」, TextureHandles[「tex_handle:int」], 「mip:int」);"

    def __init__(self, attachments:PipelineAttachments, buffer_texture:Texture, attachment:str, mip:int):
        SyntaxExpander.__init__(self)
        self.rt_handle = attachments.handle
        self.tex_handle = buffer_texture.handle
        self.attachment = attachment
        assert(mip >= 0)
        self.mip = mip


class DepthAttachment(FrameBufferAttachment):
    def __init__(self, attachments:PipelineAttachments, buffer_texture:Texture, mip:int = 0):
        FrameBufferAttachment.__init__(self, attachments, buffer_texture, "GL_DEPTH_ATTACHMENT", mip)


class ColorAttachment(FrameBufferAttachment):
    def __init__(self, attachments:PipelineAttachments, buffer_texture:Texture, index:int, mip:int = 0):
        assert(index >= 0)
        FrameBufferAttachment.__init__(self, attachments, buffer_texture, f"GL_COLOR_ATTACHMENT{str(index)}", mip)


class FramebufferLabel(SyntaxExpander):
    template = "glObjectLabel(GL_FRAMEBUFFER, FrameBufferHandles[「handle:int」], -1, \"「name:str」\");"


class CreateFrameBuffer(SyntaxExpander):
    template = """
{
	glCreateFramebuffers(1, &FrameBufferHandles[「handle:int」]);
「expanders」
}
""".strip()
    indent = ("expanders",)

    def __init__(self, attachments:PipelineAttachments):
        SyntaxExpander.__init__(self)
        self.handle = attachments.handle
        self.expanders:List[SyntaxExpander] = []
        for index, texture in enumerate(attachments.color):
            self.expanders.append(ColorAttachment(attachments, texture, index))
        if attachments.depth:
            self.expanders.append(DepthAttachment(attachments, attachments.depth[0]))
        if attachments.name is not None:
            self.expanders.append(FramebufferLabel(handle=attachments.handle, name=attachments.name))


class DeleteFrameBuffer(SyntaxExpander):
    template = "glDeleteFramebuffers(1, &FrameBufferHandles[「handle」]);"

    def __init__(self, attachments:PipelineAttachments):
        SyntaxExpander.__init__(self, handle = attachments.handle)


class SetupFrameBuffers(SyntaxExpander):
    template = """
{
「wrapped」
}
""".strip()
    indent = ("wrapped",)

    def __init__(self, framebuffers:List[PipelineAttachments]):
        SyntaxExpander.__init__(self)
        self.wrapped:List[SyntaxExpander] = [CreateFrameBuffer(a) for a in framebuffers]
