
from typing import Iterable, Union, Tuple


StatementsType = Union[str, Iterable[str]]
ArgsListType = Iterable[Tuple[str, str]]
    

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


block_template = \
"""
「prefix」
{
「body」
}「suffix」
""".strip()


def cpp_block(prefix: str, body: StatementsType, suffix: str= "") -> str:
    if type(body) is not str:
        body = "\n".join(body)
    return rewrite(block_template).format(prefix=prefix, body=indent(str(body)), suffix=suffix)


def cpp_include(name: str) -> str:
    return f"#include {name}\n"


def cpp_namespace(spacename: str, scope: StatementsType) -> str:
    prefix = f"namespace {spacename}"
    return cpp_block(prefix, scope)


def cpp_struct(name: str, members: StatementsType) -> str:
    return cpp_block(f"struct {name}", members, ";")


def cpp_op(op: str, lhs: str, rhs: str, group: bool = False) -> str:
    lp = "(" if group else ""
    rp = ")" if group else ""
    return f"{lp}{lhs} {op} {rhs}{rp}"


def cpp_decl_var(type_name: str, var_name: str) -> str:
    return f"{type_name} {var_name};"


def cpp_assign(var_name: str, value: str) -> str:
    return cpp_op("=", var_name, value) + ";"


def cpp_def_var(type_name: str, var_name: str, value: str) -> str:
    assignment = cpp_assign(var_name, value)
    return f"{type_name} {assignment}"


def cpp_fn_sig(return_type: str, function_name: str, args: ArgsListType) -> str:
    formatted_args = []
    for type_name, var_name in args:
        formatted_args.append("{} {}".format(type_name, var_name))
    args_list = ", ".join(formatted_args)
    return f"{return_type} {function_name}({args_list})"


def cpp_decl_fn(return_type: str, function_name: str, args: ArgsListType) -> str:
    fn_sig = cpp_fn_sig(return_type, function_name, args)
    return f"{fn_sig};"


def cpp_def_fn(return_type: str , function_name: str, args: ArgsListType, statements: StatementsType) -> str:
    fn_sig = cpp_fn_sig(return_type, function_name, args)
    return cpp_block(fn_sig, statements)
