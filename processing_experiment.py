
from copy import copy
from parser_experiment import *
from grammar_experiment import validate_grammar, assert_type
from graffeine.templates.OpenGL import *


class DrawDef:
    def __init__(self, name:str):
        self.name = name
        self.vs = ""
        self.fs = ""
        self.structs:List[str] = []
        self.interfaces:List[str] = []
        self.flags:Dict[str, bool] = {}

    def __repr__(self):
        return f"<DrawDef {self.name}>"


class DrawBinding:
    def __init__(self, handle_name:str):
        self.name = handle_name

    def __repr__(self):
        return f"<DrawBinding {self.name}>"


class RenderEvent:
    pass


class UploadBufferEvent(RenderEvent):
    def __init__(self, handle_name:str):
        self.name = handle_name

    def __repr__(self):
        return f"<UploadBufferEvent {self.name}>"


class DrawEvent(RenderEvent):
    def __init__(self, draw_name:str):
        self.name = draw_name
        self.bindings: List[DrawBinding] = []

    def __repr__(self):
        return f"<DrawEvent {self.name} {self.bindings}>"


class RendererDef:
    def __init__(self, renderer_name:str):
        self.name = renderer_name
        self.events : List[RenderEvent] = []

    def __repr__(self):
        return f"<RendererDef {self.name} {self.events}>"


class Program:
    def __init__(self, parser:Parser):
        self.comments:List[TokenComment] = []
        self.parser = parser
        self.structs:Dict[str, StructType] = {}
        self.interfaces:Dict[str, StructType] = {}
        self.draws:Dict[str, DrawDef] = {}
        self.handles:Dict[str, str] = {}
        self.renderers:Dict[str, RendererDef] = {}

    def buffer_index(self, handle_name:str) -> int:
        return list(self.handles.keys()).index(handle_name)

    def binding_index(self, handle_name:str) -> int:
        interface_name = self.handles[handle_name]
        return list(self.interfaces.keys()).index(interface_name)

    def shader_index(self, draw_name:str) -> int:
        return list(self.draws.keys()).index(draw_name)

    def fill_struct(self, struct_name:str, member_defs:Tuple[Token,...]) -> StructType:
        members = {}
        for member in member_defs:
            type_name, member_name = assert_type(TokenList, member).without_comments()
            if str(member_name) in members:
                self.error(f'Duplicate member name "{str(member_name)}" in struct "{struct_name}"', member_name)
            members[str(member_name)] = self.find_type(cast(TokenWord, type_name))
        return StructType(struct_name, **members)

    def fill_draw(self, draw_name:str, attrs:Tuple[Token,...], full_list:TokenList) -> DrawDef:
        draw = DrawDef(draw_name)
        for attr in attrs:
            name, value = cast(TokenList, attr).without_comments()
            if str(name) == "copy":
                if not str(value) in self.draws:
                    self.error(f'Unknown draw "{str(value)}"', value)
                other = self.draws[str(value)]
                draw.vs = other.vs
                draw.fs = other.fs
                draw.structs = copy(other.structs)
                draw.interfaces = copy(other.interfaces)
                for fkey, fvalue in other.flags.items():
                    draw.flags[fkey] = fvalue
            elif str(name) == "vs":
                draw.vs = str(value)
            elif str(name) == "fs":
                draw.fs = str(value)
            elif str(name) == "use":
                if str(value) in self.structs:
                    draw.structs.append(str(value))
                elif str(value) in self.interfaces:
                    draw.interfaces.append(str(value))
                else:
                    self.error(f'Unknown struct or interface "{str(value)}"', value)
            elif str(name) == "enable":
                draw.flags[str(value)] = True
            elif str(name) == "disable":
                draw.flags[str(value)] = False
        if draw.vs == "":
            self.error("Draw definition doesn't set the vertex shader", full_list)
        if draw.fs == "":
            self.error("Draw definition doesn't set the fragment shader", full_list)
        return draw

    def fill_renderer(self, renderer_name:str, events:Tuple[Token,...]):
        renderer = RendererDef(renderer_name)
        for event in (cast(TokenList, e).without_comments() for e in events):
            name = event[0]
            params = event[1:]
            if str(name) == "update":
                handle_name = params[0]
                if str(handle_name) not in self.handles:
                    self.error(f'Unknown handle "{str(handle_name)}"', handle_name)
                renderer.events.append(UploadBufferEvent(str(handle_name)))
            elif str(name) == "draw":
                draw_name = params[0]
                draw_splat = params[1:]
                if str(draw_name) not in self.draws:
                    self.error(f'Unknown drawdef "{str(draw_name)}"', draw_name)
                draw = DrawEvent(str(draw_name))
                for subcommand, handle_name  in (cast(TokenList, e).without_comments() for e in draw_splat):
                    assert(str(subcommand) == "bind")
                    if str(handle_name) not in self.handles:
                        self.error(f'Unknown handle "{str(handle_name)}"', handle_name)
                    draw.bindings.append(DrawBinding(str(handle_name)))
                renderer.events.append(draw)
        return renderer

    def route_command(self, command:str, token_list:TokenList):
        clean = token_list.without_comments()
        name = str(clean[1])

        if command == "struct":
            self.structs[name] = self.fill_struct(name, clean[2:])

        elif command == "interface":
            self.interfaces[name] = self.fill_struct(name, clean[2:])

        elif command == "defdraw":
            self.draws[name] = self.fill_draw(name, clean[2:], token_list)

        elif command == "defhandle":
            interface = clean[2]
            if str(interface) not in self.interfaces:
                self.error(f'Undefined interface "{str(interface)}"', interface)
            self.handles[name] = str(interface)

        elif command == "renderer":
            self.renderers[name] = self.fill_renderer(name, clean[2:])

    def process(self, tokens:Sequence[Token]):
        for token in tokens:
            if type(token) is TokenComment:
                pass
            else:
                token_list = assert_type(TokenList, token)
                command = str(token_list.without_comments()[0])
                self.route_command(command, token_list)

    def find_type(self, type_name:TokenWord) -> Optional[GlslType]:
        found = glsl_builtins.get(type_name.word) or self.structs.get(type_name.word)
        if not found:
            self.error(f"No such GLSL builtin type or struct \"{type_name.word}\"", type_name)
        return found

    def error(self, hint:str, token:Token):
        self.parser.error(hint, *token.pos(), *token.pos())


if __name__ == "__main__":
    parser = Parser()
    parser.open("example.data")
    tokens = parser.parse()
    validate_grammar(parser, tokens)
    program = Program(parser)
    program.process(tokens)

    def report(name):
        print(f" - {name}:")
        for key, value in getattr(program, name).items():
            print(f"   - {key}:", value)

    report("structs")
    report("interfaces")
    report("draws")
    report("handles")
    report("renderers")
