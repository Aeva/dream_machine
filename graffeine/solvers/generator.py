
from .intermediary import *
from ..expanders.common import *
from ..expanders.buffers import *
from ..expanders.samplers import *
from ..expanders.shaders import *
from ..expanders.drawspatch import *
from ..expanders.window import *


class FakeUpload(SyntaxExpander):
    template = """
{
	Glsl::「struct_name」 Data = { (float)(CurrentTime * 0.1) };
	Upload::「struct_name」(BufferHandles[「handle」], Data);
}
""".strip()


class Renderer(SyntaxExpander):
    template = """
void 「name」(int FrameIndex, double CurrentTime, double DeltaTime)
{
「calls」
}
""".strip()
    indent = ("calls",)


class RendererCase(SyntaxExpander):
    template = """
case 「index」:
	Renderer::「name」(FrameIndex, CurrentTime, DeltaTime);
	break;
""".strip()


class RendererSwitch(SyntaxExpander):
    template = """
switch (CurrentRenderer)
{
「cases」
default:
	HaltAndCatchFire();
}
""".strip()
    def __init__(self, program:Program):
        SyntaxExpander.__init__(self)
        self.cases = [RendererCase(index=index, name=name) for index, name in enumerate(program.renderers.keys())]


class ProgramSolver:
    def __init__(self, program:Program):
        # inputs for expanders
        self.program = program
        shaders_programs = list(map(self.expand_shader, program.draws.values()))
        shader_handles, build_shaders = solve_shaders(shaders_programs)

        interface_handles = {handle:name for (handle, name) in program.handles.items() if name in program.interfaces}
        texture_handles = {handle:name for (handle, name) in program.handles.items() if name in program.textures}

        # expanders defining the C++ struct definitions for all available structs and interfaces
        self.structs:List[SyntaxExpander] = []
        self.structs += [GlslStruct(s) for s in program.structs.values()]
        self.structs += [GlslStruct(s) for s in program.interfaces.values()]

        # expanders generated data uploader functions
        self.uploaders = [BufferUpload(program.interfaces[name]) for name in interface_handles.values()]

        # expanders for various things in the global scope
        self.globals:List[SyntaxExpander] = \
        [
            shader_handles,
            BufferHandle(len(program.handles)),
            SamplerHandles(len(program.samplers)),
        ]

        # expanders for generated code which is called after GL is initialized before rendering starts
        self.setup:List[SyntaxExpander] = \
        [
            DefaultVAO(),
        ]
        self.setup += build_shaders

        if program.handles:
            self.setup.append(CreateBuffers(handle=0, count=len(program.handles)))
            self.setup += \
            [
                BufferStorage(handle=buffer_index, bytes=program.interfaces[interface].words*4)
                for buffer_index, interface in enumerate(interface_handles.values())
            ]

        if program.samplers:
            self.setup.append(CreateSamplers(handle=0, count=len(program.samplers)))
            self.setup += \
            [
                SamplerSetup(index, sampler)
                for index, sampler in enumerate(program.samplers.values())
            ]

        # expanders defining the available renderers
        self.renderers:List[SyntaxExpander] = list(map(self.expand_renderer, program.renderers.values()))
        self.switch:SyntaxExpander = RendererSwitch(program)

    def expand_renderer_event(self, event:RenderEvent) -> SyntaxExpander:
        if type(event) == UploadBufferEvent:
            event = cast(UploadBufferEvent, event)
            return FakeUpload(
                struct_name = self.program.handles[event.name],
                handle = self.program.buffer_index(event.name))

        elif type(event) == DrawEvent:
            event = cast(DrawEvent, event)
            interface_bindings = [b for b in event.bindings if self.program.handle_is_interface(b.name)]
            texture_bindings = [b for b in event.bindings if self.program.handle_is_texture(b.name)]

            setup:List[SyntaxExpander] = \
            [
                cast(SyntaxExpander, ChangeProgram(self.program.shader_index(event.name)))
            ]
            setup += \
            [
                cast(SyntaxExpander, BindUniformBuffer(
                    binding_index = self.program.binding_index(binding.name),
                    handle = self.program.buffer_index(binding.name)))
                for binding in interface_bindings
            ]
            setup += \
            [
                cast(SyntaxExpander, Capability(flag, state))
                for (flag, state) in self.program.draws[event.name].flags.items()
            ]
            return Drawspatch(
                name = event.name,
                setup = setup,
                draw = InstancedDraw(vertices=6, instances=1))
        assert(False)
        return SyntaxExpander

    def expand_renderer(self, spec:RendererDef) -> SyntaxExpander:
        calls:List[SyntaxExpander] = [
            ColorClear(0, 0, 0),
            DepthClear(0),
        ] + [
            self.expand_renderer_event(event)
            for event in spec.events
        ]
        return Renderer(name=spec.name, calls=calls)

    def expand_shader(self, spec:DrawDef) -> ShaderProgram:
        expanders:List[SyntaxExpander] = [
            cast(SyntaxExpander, GlslStruct(self.program.structs[name]))
            for name in spec.structs
        ] + [
            cast(SyntaxExpander, UniformInterface(self.program.interfaces[name], index))
            for index, name in enumerate(self.program.interfaces) if name in spec.interfaces
        ]
        return ShaderProgram(
            spec.name,
            ShaderStage("vertex", spec.vs, expanders),
            ShaderStage("fragment", spec.fs, expanders))

    def expand(self):
        program = OpenGLWindow()
        program.window_title = "Hello World!"
        program.window_width = 512
        program.window_height = 512
        program.hint_version_major = 4
        program.hint_version_minor = 2
        program.hint_profile = "GLFW_OPENGL_CORE_PROFILE"
        program.structs = self.structs
        program.globals = self.globals
        program.uploaders = self.uploaders
        program.initial_setup_hook = self.setup
        program.renderers = self.renderers
        program.draw_frame_hook = self.switch
        return program

