
from typing import *


def CAST(_type, value):
    """
    Like cast, but you *really* mean it.
    """
    assert(type(value) == _type)
    return cast(_type, value)


def dedupe(items:list) -> list:
    """
    Removes duplicates from a list.
    This preserves the order of the list.
    """
    reduced = []
    for item in items:
        if not item in reduced:
            reduced.append(item)
    return reduced


def div_up(n:int, d:int)->int:
    """
    Integer divide and round up.
    Equivalent to: `int(ceil(float(n) / float(d)))`
    """
    return (n + d - 1) // d


def align(offset:int, alignment:int) -> int:
    """
    Align address "offset" to "alignment" units.
    For example, `align(3, 4)` would return `4`.
    """
    return div_up(offset, alignment) * alignment


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
