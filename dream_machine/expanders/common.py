
import re
import os
from collections.abc import Iterable
from ..handy import *


def external(path_part: str) -> str:
    """
    Attempts to open a file and return the contents.  This will search in the same
    directory as the calling module first, and then in the current working directory
    if no file was found.
    """
    search_dir = os.path.dirname(__file__)
    full_path = os.path.join(search_dir, path_part)
    if os.path.isfile(full_path):
        with open(full_path, "r", encoding="utf-8") as template_file:
            template = template_file.read()
        return template
    elif os.path.isfile(path_part):
        with open(path_part, "r", encoding="utf-8") as template_file:
            template = template_file.read()
        return template
    else:
        raise FileNotFoundError(f"Can't find template file \"{path_part}\"!")


def rewrite(template: str) -> str:
    """
    Alternate template syntax for string.format.  This uses 「angle quotes」 instead of
    {squiggly braces} for substitutions, so that {squiggly braces} do not need to be
    escaped.
    """
    return template.replace("{", "{{").replace("}", "}}").replace("「", "{").replace("」", "}")


class SyntaxExpanderMeta(type):
    """
    Metaclass for SyntaxExpander.
    This rewrites the "template" class variable on new classes so to use a more C++
    friendly formatting syntax, and populates the "params" class variable w/ extracted
    template parameters.  See the function "rewrite" for the exact rewrite rules.
    """
    def __new__(cls, name, bases, dct):
        newclass = super().__new__(cls, name, bases, dct)
        template = dct.get("template")
        if template:
            found = re.findall(r"「([a-zA-Z]\w+)(:[a-zA-Z]\w+)?」", template)
            params = [f[0] for f in found]
            newclass._types = {}
            for param, _type in found:
                if _type != "":
                    _type = _type[1:]
                    if param in newclass._types and newclass._types[param] != _type:
                        raise SyntaxError(f"Repeating parameter \"{param}\" has conflicting (optional) type definitions.")
                    else:
                        newclass._types[param] = _type
            newclass.params = tuple(sorted(set(params)))
            for param, _type in newclass._types.items():
                template = template.replace(f"{param}:{_type}", param)
            newclass.template = rewrite(template)
        for param in newclass.params:
            if param in ["template", "params", "indent", "_dict", "_types"]:
                raise SyntaxError(f"\"{param}\" can't be used as a parameter name in SyntaxExpander template strings.")
        return newclass


class SyntaxExpander(metaclass=SyntaxExpanderMeta):
    """
    Syntax expanders are simple templates, which are primarily intended to be used to
    generate C++ and GLSL code.
    """
    template = ""
    params: Tuple[str, ...] = tuple()
    indent: Tuple[str, ...] = tuple()
    _types: Dict[str, str] = {}

    def __init__(self, *args, **kwargs) -> None:
        if len(self.params) == 1 and len(args) > 0:
            if len(args) == 1:
                kwargs[self.params[0]] = args[0]
        elif len(self.params) > 1 and len(args) > 0:
            raise NameError(f"{type(self)} has more than one parameter, so init values have to be passed in as keyword arguments")
        self._dict = {p:"" for p in self.params}
        for key, value in kwargs.items():
            assert(key in self.params)
            self[key] = value

    def _check_type(self, key, new_value):
        if key in self._types:
            got = type(new_value).__name__
            expected = self._types[key]
            if got != expected:
                raise TypeError(f"Expected type \"{expected}\", got \"{got}\".")

    def __getitem__(self, key: str):
        if not key in self.params:
            raise KeyError(f"key \"{key}\" is not valid for {type(self).__name__}")
        return self._dict[key]

    def __setitem__(self, key: str, value: Any):
        if not key in self.params:
            raise KeyError(f"key \"{key}\" is not valid for {type(self).__name__}")
        self._check_type(key, value)
        self._dict[key] = value
        return value

    def __getattr__(self, name: str):
        try:
            return self._dict[name]
        except:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any):
        if name in self.params:
            self._check_type(name, value)
            self._dict[name] = value
        else:
            object.__setattr__(self, name, value)
        return value

    def __dir__(self):
        return sorted(set(object.__dir__(self) + list(self.params)))

    def __repr__(self) -> str:
        params_repr = ", ".join([f"{p}={repr(self._dict[p])}" for p in self.params])
        return f"<{type(self).__name__} {params_repr}>"

    def resolve(self, key: Optional[str] = None) -> str:
        if key is not None:
            value = self._dict[key]
            if type(value) is not str:
                if isinstance(value, Iterable):
                    value = "\n".join(map(str, value))
                else:
                    value = str(value)
            if key in self.indent:
                return indent(value)
            else:
                return value
        else:
            resolved = {param:self.resolve(param) for param in self.params}
            return self.template.format(**resolved)

    def __str__(self) -> str:
        return self.resolve()
