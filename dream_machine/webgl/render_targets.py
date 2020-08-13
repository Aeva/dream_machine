
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


class FrameBufferHandles(SyntaxExpander):
    template = "let FrameBufferHandles = new Array(「count:int」);"


class BindFrameBuffer(SyntaxExpander):
    template = "gl.bindFramebuffer(gl.FRAMEBUFFER, FrameBufferHandles[「handle:int」]);"

    def __init__(self, pipeline:Pipeline):
        SyntaxExpander.__init__(self, pipeline.index)


class BindBackBuffer(SyntaxExpander):
    template = "gl.bindFramebuffer(gl.FRAMEBUFFER, null);"


class FrameBufferAttachment(SyntaxExpander):
    template = "gl.framebufferTexture2D(gl.FRAMEBUFFER, 「attachment:str」, gl.TEXTURE_2D, TextureHandles[「tex_handle:int」], 「mip:int」);"

    def __init__(self, pipeline:Pipeline, output:PipelineOutput, attachment:str, mip:int):
        SyntaxExpander.__init__(self)
        self.rt_handle = pipeline.index
        self.tex_handle = output.handle
        self.attachment = attachment
        assert(mip >= 0)
        self.mip = mip


class DepthAttachment(FrameBufferAttachment):
    def __init__(self, pipeline:Pipeline, mip:int = 0):
        FrameBufferAttachment.__init__(self, pipeline, CAST(PipelineOutput, pipeline.depth_target), "gl.DEPTH_ATTACHMENT", mip)


class ColorAttachment(FrameBufferAttachment):
    def __init__(self, pipeline:Pipeline, output:PipelineOutput, mip:int = 0):
        assert(output in pipeline.color_targets)
        FrameBufferAttachment.__init__(self, pipeline, output, f"gl.COLOR_ATTACHMENT{str(output.color_index)}", mip)


class DrawBuffers(SyntaxExpander):
    template = """
gl.drawBuffers([
「attachments」
]);
""".strip()
    indent = ("attachments",)

    def __init__(self, pipeline:Pipeline):
        SyntaxExpander.__init__(self)
        attachments = []
        if pipeline.depth_target:
            attachments.append("gl.DEPTH_ATTACHMENT")
        attachments += ["gl.COLOR_ATTACHMENT{str(i)}" for i in range(len(pipeline.color_targets))]
        self.attachments = attachments


class CreateFrameBuffer(SyntaxExpander):
    template = """
{
	FrameBufferHandles[「handle:int」] = gl.createFramebuffer();
「expanders」
}
""".strip()
    indent = ("expanders",)

    def __init__(self, pipeline:Pipeline):
        SyntaxExpander.__init__(self)
        self.handle = pipeline.index
        self.expanders:List[SyntaxExpander] = []
        self.expanders.append(BindFrameBuffer(pipeline))
        for color_target in pipeline.color_targets:
            self.expanders.append(ColorAttachment(pipeline, color_target))
        if pipeline.depth_target:
            self.expanders.append(DepthAttachment(pipeline))
        if len(pipeline.color_targets) > 1:
            self.expanders.append(DrawBuffers(pipeline))
        self.expanders.append(BindBackBuffer())


class RebuildFrameBuffer(CreateFrameBuffer):
    template = """
{
	// recreate framebuffer "「name:str」"
	gl.deleteFramebuffer(FrameBufferHandles[「handle:int」]);
	FrameBufferHandles[「handle:int」] = gl.createFramebuffer();
「expanders」
}
""".strip()
    indent = ("expanders",)

    def __init__(self, pipeline:Pipeline):
        CreateFrameBuffer.__init__(self, pipeline)
        self.name = pipeline.name


class SetupFrameBuffers(SyntaxExpander):
    template = "「wrapped」"

    def __init__(self, env:Program):
        SyntaxExpander.__init__(self)
        self.wrapped:List[SyntaxExpander] = [CreateFrameBuffer(pipeline) for pipeline in env.pipelines.values() if not pipeline.uses_backbuffer]


class ResizeFrameBuffers(SyntaxExpander):
    template = """
「wrapped」
""".strip()

    def __init__(self, env:Program):
        SyntaxExpander.__init__(self)
        self.wrapped:List[SyntaxExpander] = []

        pipelines = [p for p in env.pipelines.values() if not p.uses_backbuffer]
        texture_names = sorted({out.texture.name for p in pipelines for out in p.outputs})

        for name in texture_names:
            self.wrapped.append(ResizeTexture(env.textures[name]))

        for pipeline in pipelines:
            if not pipeline.uses_backbuffer:
                self.wrapped.append(RebuildFrameBuffer(pipeline))
