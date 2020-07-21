
from .textures import *
from ..syntax.grammar import Pipeline, PipelineOutput


class FrameBufferHandles(SyntaxExpander):
    template = "GLuint FrameBufferHandles[「count」] = { 0 };"


class BindFrameBuffer(SyntaxExpander):
    template = "glBindFramebuffer(GL_FRAMEBUFFER, FrameBufferHandles[「handle:int」]);"

    def __init__(self, pipeline:Pipeline):
        SyntaxExpander.__init__(self, pipeline.index)


class BindBackBuffer(SyntaxExpander):
    template = "glBindFramebuffer(GL_FRAMEBUFFER, 0);"


class FrameBufferAttachment(SyntaxExpander):
    template = "glNamedFramebufferTexture(FrameBufferHandles[「rt_handle:int」], 「attachment:str」, TextureHandles[「tex_handle:int」], 「mip:int」);"

    def __init__(self, pipeline:Pipeline, output:PipelineOutput, attachment:str, mip:int):
        SyntaxExpander.__init__(self)
        self.rt_handle = pipeline.index
        self.tex_handle = output.handle
        self.attachment = attachment
        assert(mip >= 0)
        self.mip = mip


class DepthAttachment(FrameBufferAttachment):
    def __init__(self, pipeline:Pipeline, mip:int = 0):
        FrameBufferAttachment.__init__(self, pipeline, pipeline.depth_target, "GL_DEPTH_ATTACHMENT", mip)


class ColorAttachment(FrameBufferAttachment):
    def __init__(self, pipeline:Pipeline, output:PipelineOutput, mip:int = 0):
        assert(output in pipeline.color_targets)
        FrameBufferAttachment.__init__(self, pipeline, output, f"GL_COLOR_ATTACHMENT{str(output.color_index)}", mip)


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

    def __init__(self, pipeline:Pipeline):
        SyntaxExpander.__init__(self)
        self.handle = pipeline.index
        self.expanders:List[SyntaxExpander] = []
        for color_target in pipeline.color_targets:
            self.expanders.append(ColorAttachment(pipeline, color_target))
        if pipeline.depth_target:
            self.expanders.append(DepthAttachment(pipeline, pipeline.depth_target))
        self.expanders.append(FramebufferLabel(handle=pipeline.index, name=pipeline.name))


class DeleteFrameBuffer(SyntaxExpander):
    template = "glDeleteFramebuffers(1, &FrameBufferHandles[「handle」]);"

    def __init__(self, pipeline:Pipeline):
        SyntaxExpander.__init__(self, handle = pipeline.index)


class SetupFrameBuffers(SyntaxExpander):
    template = """
{
「wrapped」
}
""".strip()
    indent = ("wrapped",)

    def __init__(self, env:Program):
        SyntaxExpander.__init__(self)
        self.wrapped:List[SyntaxExpander] = [CreateFrameBuffer(pipeline) for pipeline in env.pipelines.values()]
