
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


from copy import copy
from ..handy import *
from ..syntax.grammar import *
from ..expanders import *
from .buffers import *
from .samplers import *
from .textures import *
from .render_targets import *
from .shaders import *
from .drawspatch import *
from .renderers import *
from .program import *
from .glsl_types import *
from .glsl_interfaces import *
from .cpp_interfaces import *
from .cpp_expressions import *


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
        if member.array is not None:
            number = CAST(TokenNumber, member.array).value
            members[member.name] = ArrayType(members[member.name], number)

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
        handle_map = {shader.encoded:index for index, shader in enumerate(shaders)}
        links = []
        for index, program in enumerate(programs):
            shader_handles = [handle_map[shader.encoded] for shader in program.shaders]
            links.append(LinkShaders(program.name, index, shader_handles))
        return links

    def solve_shader_stage(pipeline:Pipeline, stage:str) -> ShaderStage:
        shader = pipeline.shaders[stage]
        stage = {
            "vs" : "vertex",
            "fs" : "fragment",
            "cs" : "compute",
        }[stage]
        structs:List[SyntaxExpander] = [GlslStruct(solved_structs[use.struct]) for use in pipeline.structs]
        uniforms:List[SyntaxExpander] = [UniformInterface(solved_structs[u.struct], u) for u in pipeline.uniforms]
        textures:List[SyntaxExpander] = [TextureInterface(t) for t in pipeline.textures]
        images:List[SyntaxExpander] = [ImageInterface(s) for s in pipeline.sideputs]
        targets:List[SyntaxExpander] = []
        if stage == "fragment":
            if pipeline.uses_backbuffer:
                targets = [TargetInterface(None)]
            else:
                targets = [TargetInterface(c) for c in pipeline.color_targets]
        return ShaderStage(stage, shader.path, structs + uniforms + textures + images + targets)

    shaders:List[ShaderStage] = []
    programs:List[ShaderProgram] = []
    for pipeline in env.pipelines.values():
        stages:List[ShaderStage] = []
        for stage in pipeline.shaders:
            stages.append(solve_shader_stage(pipeline, stage))
        programs.append(ShaderProgram(pipeline.name, stages))
        shaders += stages

    shaders = dedupe(shaders)
    compiles: List[SyntaxExpander] = solve_shader_compilation(shaders)
    links: List[SyntaxExpander] = solve_shader_linking(shaders, programs)
    return ShaderHandles(shader_count = len(shaders), program_count=len(programs)), compiles + links


def solve_renderers(env:Program) -> Tuple[List[SyntaxExpander], Union[SyntaxExpander, str]]:
    """
    """

    def solve_draw(event:RendererDraw) -> SyntaxExpander:
        pipeline = event.pipeline
        setup:List[SyntaxExpander] = \
        [
            ChangeProgram(pipeline.index),
        ]

        if pipeline.uses_backbuffer:
            setup.append(BindBackBuffer())
        else:
            setup.append(BindFrameBuffer(pipeline))

        setup += [BindUniformBuffer(u) for u in pipeline.uniforms]
        setup += [BindTexture(t) for t in pipeline.textures]
        setup += [BindSampler(t) for t in pipeline.textures]
        setup += [BindTextureImage(s) for s in pipeline.sideputs]
        setup += \
        [
            Capability(flag.flag, flag.value())
            for flag in pipeline.flags.values()
        ]
        return Drawspatch(
            name = pipeline.name,
            setup = setup,
            draw = InstancedDraw(vertices=3, instances=1))

    def solve_dispatch(event:RendererDispatch) -> SyntaxExpander:
        pipeline = event.pipeline
        setup:List[SyntaxExpander] = \
        [
            ChangeProgram(pipeline.index),
        ]
        setup += [BindUniformBuffer(u) for u in pipeline.uniforms]
        setup += [BindTexture(t) for t in pipeline.textures]
        setup += [BindSampler(t) for t in pipeline.textures]
        setup += [BindTextureImage(s) for s in pipeline.sideputs]
        setup += \
        [
            Capability(flag.flag, flag.value())
            for flag in pipeline.flags.values()
        ]
        return Drawspatch(
            name = pipeline.name,
            setup = setup,
            draw = Dispatch(**dict(zip("xyz", event.size))))

    def solve_renderer(renderer:Renderer) -> SyntaxExpander:
        calls:List[SyntaxExpander] = [
            ColorClear(0, 0, 0),
            DepthClear(0),
        ]
        for event in renderer.children:
            if type(event) is RendererDraw:
                event = cast(RendererDraw, event)
                calls.append(solve_draw(event))
            elif type(event) is RendererDispatch:
                event = cast(RendererDispatch, event)
                calls.append(solve_dispatch(event))
            elif type(event) is RendererTextureSwap:
                event = cast(RendererTextureSwap, event)
                calls.append(SwitchTextureHandles(event.texture))
            elif type(event) is RendererRegenFrameBuffer:
                event = cast(RendererRegenFrameBuffer, event)
                calls.append(RebuildFrameBuffer(event.pipeline))

        if renderer.next:
            index = [r.name for r in env.renderers].index(renderer.next)
            calls.append(RendererAdvance(index))
        return RendererCall(name=renderer.name, calls=calls)

    if env.renderers:
        callbacks = list(map(solve_renderer, env.renderers))
        switch = RendererSwitch([RendererCase(index=i, name=r.name) for i, r in enumerate(env.renderers)])
        return callbacks, switch
    else:
        return [], ""


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
    globals:List[SyntaxExpander] = ["SDL_GLContext GLContext;"]
    if build_shaders:
        globals.append(shader_handles)

    if env.samplers:
        globals.append(SamplerHandles(len(env.samplers)))

    if env.textures:
        globals.append(TextureHandles(len(env.textures)))

    if env.pipelines:
        globals.append(FrameBufferHandles(len(env.pipelines)))

    if env.buffers:
        globals.append(BufferHandles(len(env.buffers)))

    # expanders for buffer uploaders
    upload_actions:List[SyntaxExpander] = [BufferUploadAction(s) for s in solved_structs.values()]
    upload_decls:List[SyntaxExpander] = [BufferUploadDecl(b, solved_structs) for b in env.buffers.values()]
    upload_defs:List[SyntaxExpander] = [BufferUploadDef(b, solved_structs) for b in env.buffers.values()]

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

    if env.pipelines:
        setup.append(SetupFrameBuffers(env))

    if env.buffers:
        setup.append(SetupBuffers(env, solved_structs))

    # expanders for the window resized event
    reallocate:List[SyntaxExpander] = []
    if env.pipelines:
        reallocate.append(ResizeFrameBuffers(env))

    # expanders defining the available renderers
    renderers, switch = solve_renderers(env)

    # emit the generated program
    program = GeneratedMain()
    program.window_title = "Hello World!"
    program.window_width = 512
    program.window_height = 512
    program.after_sdl_init = InitGL(4, 2)
    program.globals = globals
    program.user_var_definitions = user_vars
    program.uploader_definitions = upload_defs
    program.upload_type_handlers = upload_actions
    program.initial_setup_hook = setup
    program.resize_hook = reallocate
    program.renderers = renderers
    program.draw_frame_hook = switch

    dependencies:List[str] = ["opengl_util"]
    if len([t for t in env.textures.values() if t.src]):
        dependencies.append("images")
    header = GeneratedHeader(dependencies)
    header.struct_declarations = structs
    header.uploader_declarations = upload_decls

    extensions = \
    sorted([
        "GL_ARB_buffer_storage",
        "GL_ARB_clear_texture",
        "GL_ARB_clip_control",
        "GL_ARB_compute_shader",
        "GL_ARB_debug_output",
        "GL_ARB_direct_state_access",
        "GL_ARB_gpu_shader5",
        "GL_ARB_program_interface_query",
        "GL_ARB_shader_image_load_store",
        "GL_ARB_shader_storage_buffer_object",
        "GL_KHR_debug",
        "GL_NV_mesh_shader",
    ])

    return program, header, dependencies, extensions
