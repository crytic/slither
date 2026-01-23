from collections.abc import Callable
from slither.vyper_parsing.ast.types import (
    ASTNode,
    Module,
    ImportFrom,
    EventDef,
    AnnAssign,
    Name,
    Call,
    StructDef,
    VariableDecl,
    Subscript,
    Index,
    Hex,
    Int,
    Str,
    Tuple,
    FunctionDef,
    Assign,
    Raise,
    Attribute,
    Assert,
    Keyword,
    Arguments,
    Arg,
    UnaryOp,
    BinOp,
    Expr,
    Log,
    Return,
    VyDict,
    VyList,
    NameConstant,
    If,
    Compare,
    For,
    Break,
    Continue,
    Pass,
    InterfaceDef,
    EnumDef,
    Bytes,
    AugAssign,
    BoolOp,
)


class ParsingError(Exception):
    pass


def _extract_base_props(raw: dict) -> dict:
    return {
        "src": raw["src"],
        "node_id": raw["node_id"],
    }


def _extract_decl_props(raw: dict) -> dict:
    return {
        "doc_string": parse_doc_str(raw["doc_string"]) if raw["doc_string"] else None,
        **_extract_base_props(raw),
    }


def parse_module(raw: dict) -> Module:
    nodes_parsed: list[ASTNode] = []

    for node in raw["body"]:
        nodes_parsed.append(parse(node))

    return Module(name=raw["name"], body=nodes_parsed, **_extract_decl_props(raw))


def parse_import_from(raw: dict) -> ImportFrom:
    return ImportFrom(
        module=raw["module"],
        name=raw["name"],
        alias=raw["alias"],
        **_extract_base_props(raw),
    )


def parse_event_def(raw: dict) -> EventDef:
    body_parsed: list[ASTNode] = []
    for node in raw["body"]:
        body_parsed.append(parse(node))

    return EventDef(
        name=raw["name"],
        body=body_parsed,
        *_extract_base_props(raw),
    )


def parse_ann_assign(raw: dict) -> AnnAssign:
    return AnnAssign(
        target=parse(raw["target"]),
        annotation=parse(raw["annotation"]),
        value=parse(raw["value"]) if raw["value"] else None,
        **_extract_base_props(raw),
    )


def parse_name(raw: dict) -> Name:
    return Name(
        id=raw["id"],
        **_extract_base_props(raw),
    )


def parse_call(raw: dict) -> Call:
    return Call(
        func=parse(raw["func"]),
        args=[parse(arg) for arg in raw["args"]],
        keyword=parse(raw["keyword"]) if raw["keyword"] else None,
        keywords=[parse(keyword) for keyword in raw["keywords"]],
        **_extract_base_props(raw),
    )


def parse_struct_def(raw: dict) -> StructDef:
    body_parsed: list[ASTNode] = []
    for node in raw["body"]:
        body_parsed.append(parse(node))

    return StructDef(
        name=raw["name"],
        body=body_parsed,
        **_extract_base_props(raw),
    )


def parse_variable_decl(raw: dict) -> VariableDecl:
    return VariableDecl(
        annotation=parse(raw["annotation"]),
        value=parse(raw["value"]) if raw["value"] else None,
        target=parse(raw["target"]),
        is_constant=raw["is_constant"],
        is_immutable=raw["is_immutable"],
        is_public=raw["is_public"],
        **_extract_base_props(raw),
    )


def parse_subscript(raw: dict) -> Subscript:
    return Subscript(
        value=parse(raw["value"]),
        slice=parse(raw["slice"]),
        **_extract_base_props(raw),
    )


def parse_index(raw: dict) -> Index:
    return Index(value=parse(raw["value"]), **_extract_base_props(raw))


def parse_bytes(raw: dict) -> Bytes:
    return Bytes(value=raw["value"], **_extract_base_props(raw))


def parse_hex(raw: dict) -> Hex:
    return Hex(value=raw["value"], **_extract_base_props(raw))


def parse_int(raw: dict) -> Int:
    return Int(value=raw["value"], **_extract_base_props(raw))


def parse_str(raw: dict) -> Str:
    return Str(value=raw["value"], **_extract_base_props(raw))


def parse_tuple(raw: dict) -> ASTNode:
    return Tuple(elements=[parse(elem) for elem in raw["elements"]], **_extract_base_props(raw))


def parse_function_def(raw: dict) -> FunctionDef:
    body_parsed: list[ASTNode] = []
    for node in raw["body"]:
        body_parsed.append(parse(node))

    decorators_parsed: list[ASTNode] = []
    for node in raw["decorator_list"]:
        decorators_parsed.append(parse(node))

    return FunctionDef(
        name=raw["name"],
        args=parse_arguments(raw["args"]),
        returns=parse(raw["returns"]) if raw["returns"] else None,
        body=body_parsed,
        pos=raw["pos"],
        decorators=decorators_parsed,
        **_extract_decl_props(raw),
    )


def parse_assign(raw: dict) -> Assign:
    return Assign(
        target=parse(raw["target"]),
        value=parse(raw["value"]),
        **_extract_base_props(raw),
    )


def parse_attribute(raw: dict) -> Attribute:
    return Attribute(
        value=parse(raw["value"]),
        attr=raw["attr"],
        **_extract_base_props(raw),
    )


def parse_arguments(raw: dict) -> Arguments:
    return Arguments(
        args=[parse_arg(arg) for arg in raw["args"]],
        default=parse(raw["default"]) if raw["default"] else None,
        defaults=[parse(x) for x in raw["defaults"]],
        **_extract_base_props(raw),
    )


def parse_arg(raw: dict) -> Arg:
    return Arg(arg=raw["arg"], annotation=parse(raw["annotation"]), **_extract_base_props(raw))


def parse_assert(raw: dict) -> Assert:
    return Assert(
        test=parse(raw["test"]),
        msg=parse(raw["msg"]) if raw["msg"] else None,
        **_extract_base_props(raw),
    )


def parse_raise(raw: dict) -> Raise:
    return Raise(exc=parse(raw["exc"]) if raw["exc"] else None, **_extract_base_props(raw))


def parse_expr(raw: dict) -> Expr:
    return Expr(value=parse(raw["value"]), **_extract_base_props(raw))


# This is done for convenience so we can call `UnaryOperationType.get_type` during expression parsing.
unop_ast_type_to_op_symbol = {"Not": "!", "USub": "-"}


def parse_unary_op(raw: dict) -> UnaryOp:
    unop_str = unop_ast_type_to_op_symbol[raw["op"]["ast_type"]]
    return UnaryOp(op=unop_str, operand=parse(raw["operand"]), **_extract_base_props(raw))


# This is done for convenience so we can call `BinaryOperationType.get_type` during expression parsing.
binop_ast_type_to_op_symbol = {
    "Add": "+",
    "Mult": "*",
    "Sub": "-",
    "Div": "/",
    "Pow": "**",
    "Mod": "%",
    "BitAnd": "&",
    "BitOr": "|",
    "Shr": "<<",
    "Shl": ">>",
    "NotEq": "!=",
    "Eq": "==",
    "LtE": "<=",
    "GtE": ">=",
    "Lt": "<",
    "Gt": ">",
    "In": "In",
    "NotIn": "NotIn",
}


def parse_bin_op(raw: dict) -> BinOp:
    arith_op_str = binop_ast_type_to_op_symbol[raw["op"]["ast_type"]]
    return BinOp(
        left=parse(raw["left"]),
        op=arith_op_str,
        right=parse(raw["right"]),
        **_extract_base_props(raw),
    )


def parse_compare(raw: dict) -> Compare:
    logical_op_str = binop_ast_type_to_op_symbol[raw["op"]["ast_type"]]
    return Compare(
        left=parse(raw["left"]),
        op=logical_op_str,
        right=parse(raw["right"]),
        **_extract_base_props(raw),
    )


def parse_keyword(raw: dict) -> Keyword:
    return Keyword(arg=raw["arg"], value=parse(raw["value"]), **_extract_base_props(raw))


def parse_log(raw: dict) -> Log:
    return Log(value=parse(raw["value"]), **_extract_base_props(raw))


def parse_return(raw: dict) -> Return:
    return Return(value=parse(raw["value"]) if raw["value"] else None, **_extract_base_props(raw))


def parse_dict(raw: dict) -> ASTNode:
    return VyDict(
        keys=[parse(x) for x in raw["keys"]],
        values=[parse(x) for x in raw["values"]],
        **_extract_base_props(raw),
    )


def parse_list(raw: dict) -> VyList:
    return VyList(elements=[parse(x) for x in raw["elements"]], **_extract_base_props(raw))


def parse_name_constant(raw: dict) -> NameConstant:
    return NameConstant(value=raw["value"], **_extract_base_props(raw))


def parse_doc_str(raw: dict) -> str:
    assert isinstance(raw["value"], str)
    return raw["value"]


def parse_if(raw: dict) -> ASTNode:
    return If(
        test=parse(raw["test"]),
        body=[parse(x) for x in raw["body"]],
        orelse=[parse(x) for x in raw["orelse"]],
        **_extract_base_props(raw),
    )


def parse_for(raw: dict) -> For:
    return For(
        target=parse(raw["target"]),
        iter=parse(raw["iter"]),
        body=[parse(x) for x in raw["body"]],
        **_extract_base_props(raw),
    )


def parse_break(raw: dict) -> Break:
    return Break(**_extract_base_props(raw))


def parse_continue(raw: dict) -> Continue:
    return Continue(**_extract_base_props(raw))


def parse_pass(raw: dict) -> Pass:
    return Pass(
        **_extract_base_props(raw),
    )


def parse_interface_def(raw: dict) -> InterfaceDef:
    nodes_parsed: list[ASTNode] = []

    for node in raw["body"]:
        nodes_parsed.append(parse(node))
    return InterfaceDef(name=raw["name"], body=nodes_parsed, **_extract_base_props(raw))


def parse_enum_def(raw: dict) -> EnumDef:
    nodes_parsed: list[ASTNode] = []

    for node in raw["body"]:
        nodes_parsed.append(parse(node))

    return EnumDef(name=raw["name"], body=nodes_parsed, **_extract_base_props(raw))


aug_assign_ast_type_to_op_symbol = {
    "Add": "+=",
    "Mult": "*=",
    "Sub": "-=",
    "Div": "-=",
    "Pow": "**=",
    "Mod": "%=",
    "BitAnd": "&=",
    "BitOr": "|=",
    "Shr": "<<=",
    "Shl": ">>=",
}


def parse_aug_assign(raw: dict) -> AugAssign:
    op_str = aug_assign_ast_type_to_op_symbol[raw["op"]["ast_type"]]
    return AugAssign(
        target=parse(raw["target"]),
        op=op_str,
        value=parse(raw["value"]),
        **_extract_base_props(raw),
    )


def parse_unsupported(raw: dict) -> ASTNode:
    raise ParsingError("unsupported Vyper node", raw["ast_type"], raw.keys(), raw)


bool_op_ast_type_to_op_symbol = {"And": "&&", "Or": "||"}


def parse_bool_op(raw: dict) -> BoolOp:
    op_str = bool_op_ast_type_to_op_symbol[raw["op"]["ast_type"]]
    return BoolOp(op=op_str, values=[parse(x) for x in raw["values"]], **_extract_base_props(raw))


def parse(raw: dict) -> ASTNode:
    try:
        return PARSERS.get(raw["ast_type"], parse_unsupported)(raw)
    except ParsingError as e:
        raise e
    except Exception as e:
        raise e
        # raise ParsingError("failed to parse Vyper node", raw["ast_type"], e, raw.keys(), raw)


PARSERS: dict[str, Callable[[dict], ASTNode]] = {
    "Module": parse_module,
    "ImportFrom": parse_import_from,
    "EventDef": parse_event_def,
    "AnnAssign": parse_ann_assign,
    "Name": parse_name,
    "Call": parse_call,
    "Pass": parse_pass,
    "StructDef": parse_struct_def,
    "VariableDecl": parse_variable_decl,
    "Subscript": parse_subscript,
    "Index": parse_index,
    "Hex": parse_hex,
    "Int": parse_int,
    "Str": parse_str,
    "DocStr": parse_doc_str,
    "Tuple": parse_tuple,
    "FunctionDef": parse_function_def,
    "Assign": parse_assign,
    "Raise": parse_raise,
    "Attribute": parse_attribute,
    "Assert": parse_assert,
    "keyword": parse_keyword,
    "arguments": parse_arguments,
    "arg": parse_arg,
    "UnaryOp": parse_unary_op,
    "BinOp": parse_bin_op,
    "Expr": parse_expr,
    "Log": parse_log,
    "Return": parse_return,
    "If": parse_if,
    "Dict": parse_dict,
    "List": parse_list,
    "Compare": parse_compare,
    "NameConstant": parse_name_constant,
    "For": parse_for,
    "Break": parse_break,
    "Continue": parse_continue,
    "InterfaceDef": parse_interface_def,
    "EnumDef": parse_enum_def,
    "Bytes": parse_bytes,
    "AugAssign": parse_aug_assign,
    "BoolOp": parse_bool_op,
}
