
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


from .textures import *
from ..syntax.grammar import Pipeline, PipelineOutput


RenderTargetRewrites = Dict[str, List[Tuple[Texture, Texture]]]


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
        FrameBufferAttachment.__init__(self, pipeline, CAST(PipelineOutput, pipeline.depth_target), "GL_DEPTH_ATTACHMENT", mip)


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
            self.expanders.append(DepthAttachment(pipeline))
        self.expanders.append(FramebufferLabel(handle=pipeline.index, name=pipeline.name))


class RebuildFrameBuffer(CreateFrameBuffer):
    template = """
{
	// recreate framebuffer "「name:str」"
	glDeleteFramebuffers(1, &FrameBufferHandles[「handle:int」]);
	glCreateFramebuffers(1, &FrameBufferHandles[「handle:int」]);
「expanders」
}
""".strip()
    indent = ("expanders",)

    def __init__(self, pipeline:Pipeline):
        CreateFrameBuffer.__init__(self, pipeline)
        self.name = pipeline.name


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


class ResizeFrameBuffers(SyntaxExpander):
    template = """
「wrapped」
""".strip()

    def __init__(self, env:Program, rtv_rewrites:RenderTargetRewrites):
        SyntaxExpander.__init__(self)
        self.wrapped:List[SyntaxExpander] = []

        pipelines = [p for p in env.pipelines.values() if not p.uses_backbuffer]
        texture_names = sorted({out.texture.name for p in pipelines for out in p.outputs})
        texture_names += [t.name for r in rtv_rewrites.values() for p in r for t in p if t.name not in texture_names]

        for name in texture_names:
            texture = env.textures[name]
            self.wrapped.append(ResizeTexture(texture))
            if texture.clear:
                self.wrapped.append(ClearTexture(texture))

        for pipeline in pipelines:
            self.wrapped.append(RebuildFrameBuffer(pipeline))
