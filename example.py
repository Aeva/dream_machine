
from typing import *
from graffeine.templates.OpenGL import *
from graffeine.build import build


class TestUpload(SyntaxExpander):
    template = """
{
	Glsl::「struct_name」 TestUpload = { 0 };
	Upload::「struct_name」 (BufferHandles[「handle」], TestUpload);
}
""".strip()


class UploadData(SyntaxExpander):
    template = """
{
	Glsl::「struct_name」 Data = { 0 };
「data」
	Upload::「struct_name」 (BufferHandles[「handle」], Data);
}
""".strip()
    def __init__(self, struct: StructType, handle: int, **kwargs):
        SyntaxExpander.__init__(self)
        self.struct_name = struct.name
        self.handle = handle
        data = []
        for member, value in kwargs.items():
            assert(member in struct.members)
            data.append(f"Data.{member} = {value};")
        self.data = data


class BindUniformBuffer(SyntaxExpander):
    template = "glBindBufferBase(GL_UNIFORM_BUFFER, 「binding_index」, BufferHandles[「handle」]);"


TestStruct = StructType(
    "TestStruct",
    ElapsedTime = glsl_builtins["float"])


if __name__ == "__main__":

    interfaces:List[SyntaxExpander] = [
        UniformInterface(TestStruct),
    ]

    shader_programs = [
        ShaderProgram("draw red", ShaderStage("vertex", "shaders/splat.vs.glsl", interfaces), ShaderStage("fragment", "shaders/red.fs.glsl", interfaces)),
        ShaderProgram("draw blue", ShaderStage("vertex", "shaders/splat.vs.glsl", interfaces), ShaderStage("fragment", "shaders/blue.fs.glsl", interfaces))
    ]
    shader_handles, build_shaders = solve_shaders(shader_programs)

    struct_defs = (TestStruct,)
    structs = [GlslStruct(struct) for struct in struct_defs]

    # expressions to expand into the global scope hook
    globals:List[SyntaxExpander] = \
    [
        shader_handles,
        BufferHandle(len(struct_defs)),
    ]
    uploaders = [BufferUpload(struct) for struct in struct_defs]

    # expressions to be called after GL is intialized but before rendering starts
    setup:List[SyntaxExpander] = \
    [
        DefaultVAO(),
        Capability("GL_DEPTH_TEST", False),
        Capability("GL_CULL_FACE", False),
        Wrap([
            "glClipControl(GL_LOWER_LEFT, GL_NEGATIVE_ONE_TO_ONE);",
            "glDepthRange(1.0, 0.0);",
            "glFrontFace(GL_CCW);"
        ]),
        CreateBuffers(handle=0, count=len(struct_defs)),
    ]
    setup += build_shaders
    setup += [BufferStorage(handle=i, bytes=struct.words*4) for i, struct in enumerate(struct_defs)]
    #setup += [TestUpload(handle = i, struct_name = struct.name) for i, struct in enumerate(struct_defs)]

    # expressions to be called every frame to draw
    render:List[SyntaxExpander] = \
    [
        UploadData(TestStruct, 0, ElapsedTime="ElapsedTime"),
        BindUniformBuffer(binding_index = 0, handle = 0),
        ColorClear(0.5, 0.5, 0.5),
        DepthClear(0.0),
    ]
    render +=  list(map(lambda x: splat(*x), enumerate(shader_programs)))

    # generate the program
    program = OpenGLWindow()
    program.window_title = "Hello World!"
    program.window_width = 512
    program.window_height = 512
    program.hint_version_major = 4
    program.hint_version_minor = 2
    program.hint_profile = "GLFW_OPENGL_CORE_PROFILE"
    program.structs = structs
    program.globals = globals
    program.uploaders = uploaders
    program.initial_setup_hook = setup
    program.draw_frame_hook = render

    with open("generated.cpp", "w", encoding="utf-8") as outfile:
        outfile.write(str(program))

    build("generated.cpp", "generated.exe", debug=True)
