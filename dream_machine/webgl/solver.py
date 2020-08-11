
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


from ..handy import *
from ..syntax.grammar import *
from ..expanders import *
from .textures import *
from .shaders import *
from .drawspatch import *
from .renderers import *
from .window import *
from .glsl_interfaces import *
from .js_interfaces import *
from .js_expressions import *
from ..opengl.solver import solve_struct


splat_vs = ShaderStage("vertex", "splat.vs", [], source = """
attribute vec3 Position;
void main(void) {
  gl_Position = vec4(Position, 1.0);
}
""".strip())


class FakeUpload(SyntaxExpander):
    template = """
Upload["「struct_name」"]({
	"WindowSize" : new Float32Array([ScreenWidth, ScreenHeight, 1.0/ScreenWidth, 1.0/ScreenHeight]),
	"WindowScale" : new Float32Array([1.0, 1.0, 1.0, 1.0]),
	"ElapsedTime" : new Float32Array([CurrentTime * 0.1]),
});
""".strip()


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
            links.append(LinkShaders(program, index, shader_handles))
        return links

    def solve_shader_fs(pipeline:Pipeline) -> ShaderStage:
        shader = pipeline.shaders["fs"]
        structs:List[SyntaxExpander] = [GlslStruct(solved_structs[use.struct]) for use in pipeline.structs]
        uniforms:List[SyntaxExpander] = [UniformInterface(solved_structs[u.struct], u) for u in pipeline.uniforms]
        textures:List[SyntaxExpander] = [TextureInterface(t) for t in pipeline.textures]
        return ShaderStage("fragment", shader.path, structs + uniforms + textures)

    shaders:List[ShaderStage] = []
    programs:List[ShaderProgram] = []
    for pipeline in env.pipelines.values():
        stages:List[ShaderStage] = [splat_vs, solve_shader_fs(pipeline)]
        programs.append(ShaderProgram(pipeline, stages))
        shaders += stages

    shaders = dedupe(shaders)
    compiles: List[SyntaxExpander] = solve_shader_compilation(shaders)
    links: List[SyntaxExpander] = solve_shader_linking(shaders, programs)
    return ShaderHandles(shader_count = len(shaders), program_count=len(programs)), compiles + links


def solve_renderers(env:Program) -> Tuple[List[SyntaxExpander], SyntaxExpander]:
    """
    """

    def solve_uploader(event:RendererUpdate) -> SyntaxExpander:
        buffer = CAST(Buffer, event.buffer)
        return FakeUpload(
            struct_name = buffer.struct)

    def solve_draw(event:RendererDraw, previous:Optional[RendererDraw]) -> SyntaxExpander:
        pipeline = event.pipeline
        setup:List[SyntaxExpander] = \
        [
            ChangeProgram(pipeline.index),
        ]

        setup += [BindTexture(t) for t in pipeline.textures]

        return Drawspatch(
            setup = setup,
            draw = InstancedDraw(vertices=6, instances=1))

    def solve_renderer(renderer:Renderer) -> SyntaxExpander:
        calls:List[SyntaxExpander] = [
            ColorClear(0, 0, 0),
            DepthClear(0),
        ]
        previous_draw:Optional[RendererDraw] = None
        for event in renderer.children:
            if type(event) is RendererUpdate:
                event = cast(RendererUpdate, event)
                calls.append(solve_uploader(event))
            elif type(event) is RendererDraw:
                event = cast(RendererDraw, event)
                calls.append(solve_draw(event, previous_draw))
                previous_draw = event
        return RendererCall(name=renderer.name, calls=calls)

    callbacks = list(map(solve_renderer, env.renderers))
    switch = RendererSwitch([RendererCase(index=i, name=r.name) for i, r in enumerate(env.renderers)])
    return callbacks, switch


def solve(env:Program) -> SyntaxExpander:
    """
    Solve the webpage!
    """

    # structs
    solved_structs:Dict[str,StructType] = {k:solve_struct(v, env) for (k,v) in env.structs.items()}

    # expanders for shaders
    shader_handles, build_shaders = solve_shaders(env, solved_structs)

    # expanders for struct definitions
    structs:List[SyntaxExpander] = []

    # expanders for various things in the global scope
    globals:List[SyntaxExpander] = [shader_handles]

    if env.samplers:
        pass

    if env.textures:
        globals.append(TextureHandles(len(env.textures)))

    if env.pipelines:
        pass

    if env.buffers:
        pass

    # expanders for buffer uploaders
    uploaders:List[SyntaxExpander] = []
    if env.buffers:
        uploaders += [UploadUniformBlock(env, s) for s in solved_structs.values()]

    # user-defined variables
    user_vars:List[SyntaxExpander] = [ExternUserVar(v) for v in env.user_vars.values()]

    # expanders for generated code which is called after GL is initialized before rendering starts
    setup:List[SyntaxExpander] = \
    [
        DefaultVBO(),
    ]
    setup += build_shaders

    if env.samplers:
        pass

    if env.textures:
        setup.append(SetupTextures(env))

    if env.pipelines:
        pass

    if env.buffers:
        pass

    # expanders for the window resized event
    reallocate:List[SyntaxExpander] = []
    if env.pipelines:
        pass

    # expanders defining the available renderers
    renderers, switch = solve_renderers(env)

    # emit the generated program
    program = WebGLWindow()
    program.globals = globals
    program.uploaders = uploaders
    program.initial_setup_hook = setup
    program.resize_hook = reallocate
    program.renderers = renderers
    program.draw_frame_hook = switch
    enclosed = WebGLWindowClosure()
    enclosed.user_vars = user_vars
    enclosed.wrapped = program
    return enclosed
