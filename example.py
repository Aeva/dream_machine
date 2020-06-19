
from typing import *
import parsley
from graffeine.templates.OpenGL import *
from graffeine.build import build


grammar = parsley.makeGrammar("""
symbol = <(letterOrDigit | "_")+>:w -> w
quote = '"' <(~'"' anything)*>:w '"' -> w
string = (symbol | quote)
number = <digit+("." digit*)?>:n -> n
atom = (string | number)
list = ws '(' ws sequence:s ws ')' ws -> s
sequence = (atom|list):car (ws (atom|list))*:cdr -> [car] + cdr
""", {})


def scrub(source:str) -> str:
    """
    Remove comments.
    """
    comment = False
    scrubbed = ""
    for char in source:
        if comment and char in ["\n", "\r"]:
            comment = False
        elif char == ";":
            comment = True
        if comment:
            scrubbed += " "
        else:
            scrubbed += char
    return scrubbed


class FakeUpload(SyntaxExpander):
    template = """
{
	Glsl::「struct_name」 Data = { (float)(CurrentTime * 0.1) };
	Upload::「struct_name」(BufferHandles[「handle」], Data);
}
""".strip()


class BindUniformBuffer(SyntaxExpander):
    template = "glBindBufferBase(GL_UNIFORM_BUFFER, 「binding_index」, BufferHandles[「handle」]);"


class Renderer(SyntaxExpander):
    template = """
void 「name」(int FrameIndex, double CurrentTime, double DeltaTime)
{
「calls」
}
""".strip()
    indent = ("calls",)
    def __init__(self, name, env):
        SyntaxExpander.__init__(self)
        self.name = name
        calls = [
            ColorClear(0, 0, 0),
            DepthClear(0),
        ]
        for sexpr in env["renderers"][name]:
            if sexpr[0] == "update":
                handle_name = sexpr[1]
                handle_index = list(env["handles"].keys()).index(handle_name)
                struct_name = env["handles"][handle_name]
                calls.append(FakeUpload(struct_name = struct_name, handle=handle_index))
            if sexpr[0] == "draw":
                draw_name = sexpr[1]
                draw = env["draws"][draw_name]
                draw_index = list(env["draws"].keys()).index(draw_name)
                binds = sexpr[2:]
                event = Drawspatch()
                event.name = draw_name
                setup = [
                    ChangeProgram(draw_index),
                ]
                for bind, handle_name in binds:
                    assert(bind == "bind")
                    handle_index = list(env["handles"].keys()).index(handle_name)
                    binding_index = list(env["interfaces"].keys()).index(env["handles"][handle_name])
                    setup.append(BindUniformBuffer(binding_index=binding_index, handle=handle_index))
                for flag, state in draw.flags.items():
                    setup.append(Capability(flag, state))
                event.setup = setup
                event.draw = InstancedDraw(vertices=6, instances=1)
                calls.append(event)
        self.calls = calls


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
    def __init__(self, env):
        SyntaxExpander.__init__(self)
        self.cases = [RendererCase(index=index, name=name) for index, name in enumerate(env["renderers"].keys())]


class DrawDef:
    def __init__(self, env, name, params):
        self.name = name
        self.vs = ""
        self.fs = ""
        self.structs = []
        self.interfaces = []
        self.flags = {}
        for key, value in params:
            if key == "copy":
                other = env["draws"][value]
                self.vs = other.vs
                self.fs = other.fs
                self.structs += other.structs
                self.interfaces += other.interfaces
                for fkey, fvalue in other.flags.items():
                    self.flags[fkey] = fvalue
            elif key == "vs":
                self.vs = value
            elif key == "fs":
                self.fs = value
            elif key == "use":
                if value in env["structs"]:
                    self.structs.append(value)
                else:
                    assert(value in env["interfaces"])
                    self.interfaces.append(value)
            elif key == "enable":
                self.flags[value] = True
            elif key == "disable":
                self.flags[value] = False

    def make_program(self, env):
        binding_points = {k:i for i, k in enumerate(env["interfaces"].keys())}
        structs = [GlslStruct(env["structs"][s]) for s in self.structs]
        interfaces = [UniformInterface(env["interfaces"][i], binding_points[i]) for i in self.interfaces]
        expanders = structs + interfaces
        vert = ShaderStage("vertex", self.vs, expanders)
        frag = ShaderStage("fragment", self.fs, expanders)
        return ShaderProgram(self.name, vert, frag)


def parse(path:str):
    with open(path, "r") as file:
        source = file.read()
    scrubbed = scrub(source)

    parsed = grammar(scrubbed).sequence()
    defs = {
        "struct" : {},
        "interface" : {},
        "defdraw" : {},
        "defhandle" : {},
        "renderer" : {},
    }

    for sexpr in parsed:
        assert(type(sexpr) is list)
        assert(sexpr[0] in ["struct", "interface", "defdraw", "defhandle", "renderer"])
        key, name = sexpr[:2]
        params = sexpr[2:]
        defs[key][name] = params

    env = {
        "structs" : {},
        "interfaces" : {},
        "draws" : {},
        "handles" : {},
        "renderers" : {},
    }

    def fill_struct(name, members):
        find = lambda t: glsl_builtins.get(t) or env["structs"].get(t)
        members = {m_name : find(m_type) for m_type, m_name in members}
        return StructType(name, **members)

    for name, members in defs["struct"].items():
        env["structs"][name] = fill_struct(name, members)

    for name, members in defs["interface"].items():
        env["interfaces"][name] = fill_struct(name, members)

    for name, params in defs["defdraw"].items():
        env["draws"][name] = DrawDef(env, name, params)

    for name, params in defs["defhandle"].items():
        interface = params[0]
        assert(interface in env["interfaces"])
        env["handles"][name] = interface

    for name, params in defs["renderer"].items():
        env["renderers"][name] = params

    return env


if __name__ == "__main__":
    env = parse("example.data")
    
    shader_programs = [draw.make_program(env) for draw in env["draws"].values()]
    shader_handles, build_shaders = solve_shaders(shader_programs)

    structs:List[SyntaxExpander] = []
    structs += [GlslStruct(s) for s in env["structs"].values()]
    structs += [GlslStruct(i) for i in env["interfaces"].values()]

    # expressions to expand into the global scope hook
    globals:List[SyntaxExpander] = \
    [
        shader_handles,
        BufferHandle(len(env["handles"])),
    ]
    uploaders = [BufferUpload(env["interfaces"][i]) for i in set(env["handles"].values())]

    # expressions to be called after GL is intialized but before rendering starts
    setup:List[SyntaxExpander] = \
    [
        DefaultVAO(),
        #Capability("GL_DEPTH_TEST", False),
        #Capability("GL_CULL_FACE", False),
        #Wrap([
        #    "glClipControl(GL_LOWER_LEFT, GL_NEGATIVE_ONE_TO_ONE);",
        #    "glDepthRange(1.0, 0.0);",
        #    "glFrontFace(GL_CCW);"
        #]),
        CreateBuffers(handle=0, count=len(env["handles"])),
    ]
    setup += build_shaders
    setup += [BufferStorage(handle=handle, bytes=env["interfaces"][struct].words*4) for handle, struct in enumerate(env["handles"].values())]

    # 
    renders:List[SyntaxExpander] = [Renderer(name, env) for name in env["renderers"].keys()]

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
    program.renderers = renders
    program.draw_frame_hook = RendererSwitch(env)

    with open("generated.cpp", "w", encoding="utf-8") as outfile:
        outfile.write(str(program))

    build("generated.cpp", "generated.exe", debug=True)
