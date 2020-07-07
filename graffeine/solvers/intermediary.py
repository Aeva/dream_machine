
from copy import copy
from ..handy import *
from ..syntax.tokens import *
from ..syntax.parser import Parser
from ..syntax.grammar import validate_grammar
from ..expanders.glsl_types import *


class Sampler:
    def __init__(self, name:str):
        self.name = name
        self.min_filter:str = ""
        self.mag_filter:str = ""


class Texture:
    def __init__(self, name:str):
        self.name = name
        self.sampler:str = ""
        self.format:str = ""


class Texture2D(Texture):
    VALID_FORMATS = [
        "RGBA8",
        "RGBA32F",
    ]
    def __init__(self, name:str):
        Texture.__init__(self, name)


class DrawDef:
    def __init__(self, name:str):
        self.name = name
        self.vs = ""
        self.fs = ""
        self.structs:List[str] = []
        self.interfaces:List[str] = []
        self.textures:List[str] = []
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
        self.samplers:Dict[str, Sampler] = {}
        self.textures:Dict[str, Texture] = {}
        self.preloads:Dict[str, str] = {}
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
            type_name, member_name = CAST(TokenList, member).without_comments()
            if str(member_name) in members:
                self.error(f'Duplicate member name "{str(member_name)}" in struct "{struct_name}"', member_name)
            members[str(member_name)] = self.find_type(cast(TokenWord, type_name))
        return StructType(struct_name, **members)

    def fill_sampler(self, sampler_name:str, attrs:Tuple[Token,...], full_list:TokenList) -> Sampler:
        if self.samplers.get(sampler_name):
            self.error(f'"Multiple definitions of sampler "{sampler_name}"', full_list)
        sampler = Sampler(sampler_name)
        for attr in attrs:
            param, value = cast(TokenList, attr).without_comments()
            filter = str(param)
            assert(filter in ["min_filter", "mag_filter"])
            current_value = getattr(sampler, filter)
            if current_value != "":
                self.error("Duplicate filter definition.", attr)
            elif str(value) not in ["GL_NEAREST", "GL_LINEAR"]:
                self.error(f'Unsupported {filter} value: "{str(value)}"', value)
            else:
                setattr(sampler, filter, str(value))

        if sampler.min_filter == "":
            self.error("Missing min_filter definition", full_list)
        if sampler.mag_filter == "":
            self.error("Missing mag_filter definition", full_list)

        return sampler

    def fill_texture2d(self, texture_name:str, attrs:Tuple[Token,...], full_list:TokenList) -> Texture:
        if self.textures.get(texture_name):
            self.error(f'"Multiple definitions of texture "{texture_name}"', full_list)
        texture = Texture2D(texture_name)
        for attr in attrs:
            param, value = cast(TokenList, attr).without_comments()

            if str(param) == "use":
                if texture.sampler != "":
                    self.error(f'Texture "{texture_name}" has multiple sampler definitions.  See "use" entries.', full_list)
                sampler_name = str(value)
                if self.samplers.get(sampler_name) is None:
                    self.error(f'Unknown sampler "{sampler_name}"', attr)
                texture.sampler = sampler_name

            elif str(param) == "format":
                if texture.format != "":
                    self.error(f'Texture "{texture_name}" has multiple format definitions.', full_list)
                format = str(value)
                if not format in Texture2D.VALID_FORMATS:
                    self.error(f'Unsupported format "{format}".', attr)
                texture.format = format

        if texture.sampler == "":
            self.error("Texture must use a sampler.", full_list)
        if texture.format == "":
            self.error("Missing texture format.", full_list)

        return texture

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
                elif str(value) in self.textures:
                    draw.textures.append(str(value))
                else:
                    self.error(f'Unknown struct or interface or texture "{str(value)}"', value)
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

        elif command == "sampler":
            self.samplers[name] = self.fill_sampler(name, clean[2:], token_list)

        elif command == "texture2d":
            self.textures[name] = self.fill_texture2d(name, clean[2:], token_list)

        elif command == "pipeline":
            self.draws[name] = self.fill_draw(name, clean[2:], token_list)

        elif command == "handle":
            interface = clean[2]
            if str(interface) not in self.interfaces:
                self.error(f'Undefined interface "{str(interface)}"', interface)
            self.handles[name] = str(interface)

        elif command == "preload":
            handle = clean[2]
            path = clean[3]
            if str(handle) not in self.handles:
                self.error(f'Undefined handle "{str(handle)}"', handle)
            elif str(handle) in self.preloads:
                self.error(f'Multiple preloads reference handle "{str(handle)}"', handle)
            else:
                self.preloads[handle] = str(path)

        elif command == "renderer":
            self.renderers[name] = self.fill_renderer(name, clean[2:])

    def process(self, tokens:Sequence[Token]):
        for token in tokens:
            if type(token) is TokenComment:
                pass
            else:
                token_list = CAST(TokenList, token)
                command = str(token_list.without_comments()[0])
                self.route_command(command, token_list)

    def find_type(self, type_name:TokenWord) -> Optional[GlslType]:
        found = glsl_builtins.get(type_name.word) or self.structs.get(type_name.word)
        if not found:
            self.error(f"No such GLSL builtin type or struct \"{type_name.word}\"", type_name)
        return found

    def error(self, hint:str, token:Token):
        self.parser.error(hint, *token.pos(), *token.pos())
