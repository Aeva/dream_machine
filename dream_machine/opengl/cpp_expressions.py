
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


BINARY_REWRITE = \
{
    "add" : "+",
    "sub" : "-",
    "mul" : "*",
    "div" : "/",
}


class BinaryExpander(SyntaxExpander):
    template = "(「lhs」 「op」 「rhs」)"

    def __init__(self, cmd:str, args:list):
        SyntaxExpander.__init__(self)
        self.op = BINARY_REWRITE[cmd]
        if len(args) == 2:
            print("args:", args)
            self.lhs = solve_expression(args[0])
            self.rhs = solve_expression(args[1])
        else:
            assert(len(args)) > 2
            self.lhs = BinaryExpander(cmd, args[:-1])
            self.rhs = solve_expression(args[-1])


class CallExpander(SyntaxExpander):
    template = "「cmd」(「args」)"

    def __init__(self, cmd:str, args:list):
        SyntaxExpander.__init__(self)
        self.cmd = cmd
        self.args = ", ".join([str(solve_expression(a)) for a in args])


class ValueExpander(SyntaxExpander):
    template = "「wrapped」"


def solve_expression(expr:Any) -> SyntaxExpander:
    if type(expr) is str and expr not in COMMON_VARS:
        expr = f'UserVars::{expr}'
    if type(expr) in (int, float, str):
        return ValueExpander(expr)
    else:
        expr = CAST(UnfoldedExpression, expr)
        if expr.cmd in BINARY_REWRITE:
            return BinaryExpander(expr.cmd, expr.args)
        else:
            return CallExpander(expr.cmd, expr.args)


class ExternUserVar(SyntaxExpander):
    template = "extern 「type」 「name」 = 「value」;"
    def __init__(self, user_var:UserVar):
        SyntaxExpander.__init__(self)
        self.type = user_var.ctype
        self.name = user_var.name
        self.value = solve_expression(user_var.value)
