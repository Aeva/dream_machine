
import sys
assert(sys.version_info.major >= 3)
assert(sys.version_info.minor >= 6)
from enum import Enum


RTV_LOOKUP = {}


class Buffer:
    pass


class PixelFormat(Enum):
    RGBA_8 = 1
    RGBA_32 = 2


class Texture2D:
    def __init__(self,
                 width,
                 height,
                 format,
                 name = None):
        self.width = width
        self.height = height
        self.format = format
        self.name = name


class Sampler:
    class Filter(Enum):
        NEAREST = 1
        LINEAR = 2

    class Wrap(Enum):
        CLAMP = 1
        REPEAT = 2
        MIRROR = 3

    def __init__(self,
                 min_filter = Filter.LINEAR,
                 mag_filter = Filter.LINEAR,
                 wrap_s = Wrap.CLAMP,
                 wrap_t = Wrap.CLAMP,
                 wrap_r = Wrap.CLAMP,
                 ):
        self.min_filter = min_filter
        self.mag_filter = mag_filter
        self.wrap_s = wrap_s
        self.wrap_t = wrap_t
        self.wrap_r = wrap_r


class DepthTarget:
    pass


class ColorTarget:
    def __init__(self, format = PixelFormat.RGBA_8):
        self.format = format


class TextureView:
    def __init__(self, texture, sampler = None):
        self.texture = texture
        self.sampler = sampler or Sampler()


class MetaDrawspatch(type):
    global RTV_LOOKUP
    global SRV_LOOKUP

    def __new__(cls, name, bases, dct):
        newclass = super().__new__(cls, name, bases, dct)
        for attr in map(lambda x: getattr(newclass, x), dir(newclass)):
            if type(attr) in (DepthTarget, ColorTarget):
                RTV_LOOKUP[attr] = newclass
        return newclass


class ImpossibleOrdering(Exception):
    pass


class Drawspatch(metaclass=MetaDrawspatch):
    def validate(drawspatch, before, after):
        for attr, attr_name in [(getattr(drawspatch, name), name) for name in dir(drawspatch)]:
            if type(attr) in (TextureView, ):
                if type(attr.texture) in (DepthTarget, ColorTarget):
                    dependency = RTV_LOOKUP[attr.texture]
                    if dependency not in before:
                        srv_name = f"{drawspatch.__name__}.{attr_name}"
                        msg = f"{srv_name} requires {dependency.__name__} to be drawn before {drawspatch.__name__}"
                        raise ImpossibleOrdering(msg)


class DrawCall(Drawspatch):
    def validate(drawspatch, before, after):
        Drawspatch.validate(drawspatch, before, after)


def compile(namespace, *drawspatches):
    validated = []
    for i, drawspatch in enumerate(drawspatches):
        remaining = drawspatches[i+1:]
        drawspatch.validate(drawspatch, validated, remaining)
        validated.append(drawspatch)
