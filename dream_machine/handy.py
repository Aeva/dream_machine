
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


from typing import *
from collections import abc


def is_sequence(value:Any) -> bool:
    return isinstance(value, abc.Sequence)


def is_mapping(value:Any) -> bool:
    return isinstance(value, abc.Mapping)


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
