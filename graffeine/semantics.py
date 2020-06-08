
import os
import weakref
from template_tools import *


class Shader:
    def __init__(self):
        self.path = None
        self.type = None

    def validate(self):
        if os.path.is_file(self.path):
            return True
        else:
            raise ValueError(f"Invalid shader path: {self.path}")


class Texture:
    def __init__(self):
        self.path = None


class Texture2D:
    def __init__(self):
        Texture.__init__(self)
        self.format = None
        self.size(0, 0)

    def validate(self):
        pass


class Sampler:
    def __init__(self):
        pass

    def validate(self):
        pass


class RenderTarget:
    def __init__(self):
        self.drawspatch = None
        self.name = None
        self.format = None
        self.texture = None

    def expand_texture(self):
        if self.texture is None:
            self.texture = Texture2D()
            self.texture.size = self.drawspatch().size
            self.texture.format = self.format
        return self.texture


class Drawspatch:
    def __init__(self):
        self.name = None
        self.uniforms = {}
        self.textures = {}
        self.samplers = {}

    def validate(self):
        pass


class DrawCall(Drawspatch):
    def __init__(self):
        Drawspatch.__init__(self)
        self.vertex_shader = None
        self.fragment_shader = None
        self.offset = (0, 0)
        self.size = (0, 0)
        self.state = {}
        self.rendertargets = {}

    def get_rt_texture(self, index):
        if index in self.rt_textures:
            return self.rt_textures[index]
        else:
            tex = Texture2D()
            tex.size = size
            self.rt_textures[index] = tex
            return tex

    def expand(self):
        for name, value in self.textures.items():
            if not issubclass(type(value), Texture):
                assert(type(value) is RenderTarget)
                self.textures[name] = value.expand_texture()

    def validate(self):
        pass
