
import re
import os
from typing import Iterable, Tuple, Optional
from collections.abc import Iterable


def external(path_part: str) -> str:
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
        raise RuntimeError(f"Can't find template file \"{path_part}\"!")


def rewrite(template: str) -> str:
    """
    Alternate template syntax for string.format.  This uses 「angle quotes」 instead of
    {squiggly braces} for substitutions, so that {squiggly braces} do not need to be
    escaped.
    """
    return template.replace("{", "{{").replace("}", "}}").replace("「", "{").replace("」", "}")


def indent(text: str) -> str:
    """
    Indent each line in a string.
    """
    lines = text.replace("\r", "").split("\n")
    new_lines = []
    for line in lines:
        if len(line.strip()) == 0:
            new_lines.append("")
        else:
            new_lines.append("\t" + line)
    return "\n".join(new_lines)


class SyntaxExpanderMeta(type):
    def __new__(cls, name, bases, dct):
        newclass = super().__new__(cls, name, bases, dct)
        if newclass.template:
            newclass.params = tuple(sorted(set(re.findall(r"「([a-zA-Z]\w+)」", newclass.template))))
            newclass.template = rewrite(newclass.template)
        return newclass


class SyntaxExpander(metaclass=SyntaxExpanderMeta):
    template = ""
    params: Tuple[str, ...] = tuple()
    indent: Tuple[str, ...] = tuple()

    def __init__(self, *args, **kwargs) -> None:
        if len(self.params) == 1 and len(args) > 0:
            if len(args) == 1:
                kwargs[self.params[0]] = args[0]
        elif len(self.params) > 1 and len(args) > 0:
            raise NameError(f"{type(self)} has more than one parameter, so init values have to be passed in as keyword arguments")
        self._dict = dict(zip(self.params, ["" for p in self.params]))
        for key, value in kwargs.items():
            self[key] = value

    def __getitem__(self, key: str) -> str:
        if not key in self.params:
            raise KeyError(f"key \"{key}\" is not valid for {type(self)}")
        return self._dict[key]

    def __setitem__(self, key: str, value: str) -> str:
        if not key in self.params:
            raise KeyError(f"key \"{key}\" is not valid for {type(self).__name__}")
        self._dict[key] = value
        return value

    def __getattr__(self, name):
        if name in self.params:
            return self[name]
        else:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in self.params:
            self[name] = value
        else:
            object.__setattr__(self, name, value)
        return value

    def __dir__(self):
        return sorted(list(set(object.__dir__(self) + list(self.params))))

    def __repr__(self) -> str:
        params_repr = ", ".join([f"{p}={repr(self._dict[p])}" for p in self.params])
        return f"<{type(self).__name__} {params_repr}>"

    def resolve(self, key: Optional[str] = None) -> str:
        if key is not None:
            value = self._dict[key]
            if type(value) is not str:
                if isinstance(value, Iterable):
                    value = "\n".join(map(lambda x: str(x), value))
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
