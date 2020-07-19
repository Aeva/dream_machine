﻿
from .handy import *
from .expanders.common import *
from .expanders.buffers import *
from .expanders.samplers import *
from .expanders.textures import *
from .expanders.render_targets import *
from .expanders.shaders import *
from .expanders.drawspatch import *
from .expanders.renderers import *
from .expanders.window import *
from .expanders.glsl_types import *
from .expanders.glsl_interfaces import *
from .expanders.cpp_interfaces import *
from .expanders.cpp_expressions import *
from .syntax.grammar import *


class FakeUpload(SyntaxExpander):
    template = """
{
	Glsl::「struct_name」 Data = { (float)(CurrentTime * 0.1) };
	Upload::「struct_name」(BufferHandles[「handle」], Data);
}
""".strip()


def solve_struct(struct:Struct, env:Program) -> StructType:
    """
    Attempt to solve a struct's layout.  When the struct references other
    structs, this will simply recurse.  If the maximum recursion depth is
    reached, then throw a validation error.
    """
    members = {}
    for member in struct.members:
        if member.type in glsl_builtins:
            members[member.name] = glsl_builtins[member.type]
        else:
            assert(member.type in env.structs)
            try:
                members[member.name] = solve_struct(env.structs[member.type], env)
            except RecursionError:
                struct.error(f'Circular reference w/ other structs via member "{member.name}".')
    return StructType(struct.name, **members)


def solve_shaders(env:Program, solved_structs:Dict[str,StructType]) -> Tuple[ShaderHandles, List[SyntaxExpander]]:
    """
    This function returns a ShaderHandles expander (which should go in the
    generated program's global scope), and a list of CompileShader and
    LinkShaders expanders (which produce code that should be called after the
    OpenGL context is initialized, but before the shaders are to be used).
    """

    def solve_shader_compilation(shaders: List[ShaderStage]):
        return [CompileShader(*args) for args in enumerate(shaders)]

    def solve_shader_linking(shaders: List[ShaderStage], programs: List[ShaderProgram]):
        handle_map = {shader:index for index, shader in enumerate(shaders)}
        links = []
        for index, program in enumerate(programs):
            shader_handles = [handle_map[shader] for shader in program.shaders]
            links.append(LinkShaders(program.name, index, shader_handles))
        return links

    def solve_shader_stage(pipeline:Pipeline, stage:str) -> ShaderStage:
        shader = pipeline.shaders[stage]
        stage = {
            "vs" : "vertex",
            "fs" : "fragment",
            "cs" : "compute",
        }[stage]
        structs:List[SyntaxExpander] = \
        [
            GlslStruct(solved_structs[use.struct])
            for use in pipeline.structs
        ]
        uniforms:List[SyntaxExpander] = \
        [
            UniformInterface(solved_structs[uniform.type], binding, uniform.name)
            for (binding, uniform) in enumerate(pipeline.uniforms())
        ]
        textures:List[SyntaxExpander] = \
        [
            TextureInterface(t) for t in pipeline.textures()
        ]
        return ShaderStage(stage, shader.path, structs + uniforms + textures)

    shaders:List[ShaderStage] = []
    programs:List[ShaderProgram] = []
    for pipeline in env.pipelines.values():
        stages:List[ShaderStage] = []
        for stage in pipeline.shaders:
            stages.append(solve_shader_stage(pipeline, stage))
        programs.append(ShaderProgram(pipeline.name, stages))
        shaders += stages

    shaders = dedupe(shaders)
    paths = ",\n".join([f'"{shader.save()}"' for shader in shaders])
    compiles: List[SyntaxExpander] = solve_shader_compilation(shaders)
    links: List[SyntaxExpander] = solve_shader_linking(shaders, programs)
    return ShaderHandles(shader_count = len(shaders), program_count=len(programs), paths=paths), compiles + links


def solve_renderers(env:Program) -> Tuple[List[SyntaxExpander], SyntaxExpander]:
    """
    """

    def solve_uploader(event:RendererUpdate) -> SyntaxExpander:
        return FakeUpload(
            struct_name = event.buffer.struct,
            handle = event.buffer.handle)

    def solve_draw(event:RendererDraw) -> SyntaxExpander:
        program_handle = list(env.pipelines.keys()).index(event.pipeline)
        pipeline = env.pipelines[event.pipeline]

        setup:List[SyntaxExpander] = \
        [
            ChangeProgram(program_handle),
        ]

        if (pipeline.attachments):
            setup.append(BindFrameBuffer(pipeline.attachments))
        else:
            setup.append(BindBackBuffer())

        setup += \
        [
            BindUniformBuffer(
                binding_index = pipeline.binding_index(binding.name),
                handle = binding.buffer.handle)
            for binding in event.buffer_bindings()
        ]
        setup += \
        [
            BindTexture(t) for t in event.texture_bindings()
        ]

        explicit_samplers = {b.name:b for b in event.sampler_bindings()}
        implicit_samplers = {b.name:b for b in event.texture_bindings() if b.name not in explicit_samplers}
        sampler_bindings = list(implicit_samplers.values()) + list(explicit_samplers.values())
        setup += \
        [
            BindSampler(t) for t in sampler_bindings
        ]
        setup += \
        [
            Capability(flag.flag, flag.value())
            for flag in pipeline.flags.values()
        ]
        return Drawspatch(
            name = event.pipeline,
            setup = setup,
            draw = InstancedDraw(vertices=6, instances=1))

    def solve_renderer(renderer:Renderer) -> SyntaxExpander:
        calls:List[SyntaxExpander] = [
            ColorClear(0, 0, 0),
            DepthClear(0),
        ]
        for event in renderer.children:
            if type(event) is RendererUpdate:
                calls.append(solve_uploader(event))
            elif type(event) is RendererDraw:
                calls.append(solve_draw(event))
        return RendererCall(name=renderer.name, calls=calls)

    callbacks = list(map(solve_renderer, env.renderers))
    switch = RendererSwitch([RendererCase(index=i, name=r.name) for i, r in enumerate(env.renderers)])
    return callbacks, switch


def solve(env:Program) -> SyntaxExpander:
    """
    Solve the program!
    """

    # structs
    solved_structs:Dict[str,StructType] = {k:solve_struct(v, env) for (k,v) in env.structs.items()}

    # expanders for shaders
    shader_handles, build_shaders = solve_shaders(env, solved_structs)

    # expanders for struct definitions
    structs:List[SyntaxExpander] = []
    if solved_structs:
        structs += [GlslStruct(s) for s in solved_structs.values()]

    # expanders for various things in the global scope
    globals:List[SyntaxExpander] = [shader_handles]

    if env.samplers:
        globals.append(SamplerHandles(len(env.samplers)))

    if env.textures:
        globals.append(TextureHandles(len(env.textures)))

    framebuffers = env.pipeline_attachments
    if framebuffers:
        globals.append(FrameBufferHandles(len(framebuffers)))

    if env.buffers:
        globals.append(BufferHandles(len(env.buffers)))

    # expanders for buffer uploaders
    uploaders:List[SyntaxExpander] = []
    if env.buffers:
        uploaders += [BufferUpload(s) for s in solved_structs.values()]

    # user-defined variables
    user_vars:List[SyntaxExpander] = [ExternUserVar(v) for v in env.user_vars.values()]

    # expanders for generated code which is called after GL is initialized before rendering starts
    setup:List[SyntaxExpander] = \
    [
        DefaultVAO(),
    ]
    setup += build_shaders

    if env.samplers:
        setup.append(SetupSamplers(env))

    if env.textures:
        setup.append(SetupTextures(env))

    if framebuffers:
        setup.append(SetupFrameBuffers(framebuffers))

    if env.buffers:
        setup.append(SetupBuffers(env, solved_structs))

    # expanders defining the available renderers
    renderers, switch = solve_renderers(env)

    # emit the generated program
    program = OpenGLWindow()
    program.window_title = "Hello World!"
    program.window_width = 512
    program.window_height = 512
    program.hint_version_major = 4
    program.hint_version_minor = 2
    program.hint_profile = "GLFW_OPENGL_CORE_PROFILE"
    program.structs = structs
    program.globals = globals
    program.user_vars = user_vars
    program.uploaders = uploaders
    program.initial_setup_hook = setup
    program.renderers = renderers
    program.draw_frame_hook = switch
    return program