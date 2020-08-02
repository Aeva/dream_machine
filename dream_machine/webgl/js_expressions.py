
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
from ..expanders import SyntaxExpander
from ..handy import *
from ..syntax.grammar import UserVar, COMMON_VARS
from ..syntax.arithmetic import UnfoldedExpression
from ..opengl.cpp_expressions import BINARY_REWRITE, BinaryExpander, CallExpander, ValueExpander


def solve_expression(expr:Any) -> SyntaxExpander:
    if type(expr) is str and expr not in COMMON_VARS:
        expr = f'UserVars.{expr}'
    if type(expr) in (int, float, str):
        return ValueExpander(expr)
    else:
        expr = CAST(UnfoldedExpression, expr)
        if expr.cmd in BINARY_REWRITE:
            return BinaryExpander(expr.cmd, expr.args)
        else:
            return CallExpander(expr.cmd, expr.args)


class ExternUserVar(SyntaxExpander):
    template = "「name」 : 「value」,"
    def __init__(self, user_var:UserVar):
        SyntaxExpander.__init__(self)
        self.type = user_var.ctype
        self.name = user_var.name
        self.value = solve_expression(user_var.value)
