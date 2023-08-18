import logging
import re
from typing import Union, Dict, TYPE_CHECKING, List, Any

import slither.core.expressions.type_conversion
from slither.core.declarations.solidity_variables import (
    SOLIDITY_VARIABLES_COMPOSED,
    SolidityVariableComposed,
)
from slither.core.declarations import SolidityFunction
from slither.core.expressions import (
    CallExpression,
    ConditionalExpression,
    ElementaryTypeNameExpression,
    Identifier,
    IndexAccess,
    Literal,
    MemberAccess,
    NewArray,
    NewContract,
    NewElementaryType,
    SuperCallExpression,
    SuperIdentifier,
    TupleExpression,
    TypeConversion,
    UnaryOperation,
    UnaryOperationType,
)
from slither.core.expressions.assignment_operation import (
    AssignmentOperation,
    AssignmentOperationType,
)
from slither.core.expressions.binary_operation import (
    BinaryOperation,
    BinaryOperationType,
)
from slither.core.solidity_types import (
    ArrayType,
    ElementaryType,
    UserDefinedType,
)
from slither.solc_parsing.declarations.caller_context import CallerContextExpression
from slither.solc_parsing.exceptions import ParsingError, VariableNotFound
from slither.vyper_parsing.expressions.find_variable import find_variable
from slither.solc_parsing.solidity_types.type_parsing import UnknownType, parse_type


if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression

logger = logging.getLogger("ExpressionParsing")

# pylint: disable=anomalous-backslash-in-string,import-outside-toplevel,too-many-branches,too-many-locals

# region Filtering
###################################################################################
###################################################################################


def filter_name(value: str) -> str:
    value = value.replace(" memory", "")
    value = value.replace(" storage", "")
    value = value.replace(" external", "")
    value = value.replace(" internal", "")
    value = value.replace("struct ", "")
    value = value.replace("contract ", "")
    value = value.replace("enum ", "")
    value = value.replace(" ref", "")
    value = value.replace(" pointer", "")
    value = value.replace(" pure", "")
    value = value.replace(" view", "")
    value = value.replace(" constant", "")
    value = value.replace(" payable", "")
    value = value.replace("function (", "function(")
    value = value.replace("returns (", "returns(")
    value = value.replace(" calldata", "")

    # remove the text remaining after functio(...)
    # which should only be ..returns(...)
    # nested parenthesis so we use a system of counter on parenthesis
    idx = value.find("(")
    if idx:
        counter = 1
        max_idx = len(value)
        while counter:
            assert idx < max_idx
            idx = idx + 1
            if value[idx] == "(":
                counter += 1
            elif value[idx] == ")":
                counter -= 1
        value = value[: idx + 1]
    return value


# endregion

###################################################################################
###################################################################################
# region Parsing
###################################################################################
###################################################################################

# pylint: disable=too-many-statements
def parse_call(
    expression: Dict, caller_context
) -> Union[
    slither.core.expressions.call_expression.CallExpression,
    slither.core.expressions.type_conversion.TypeConversion,
]:
    src = expression["src"]
    if caller_context.is_compact_ast:
        attributes = expression
        type_conversion = expression["kind"] == "typeConversion"
        type_return = attributes["typeDescriptions"]["typeString"]

    else:
        attributes = expression["attributes"]
        type_conversion = attributes["type_conversion"]
        type_return = attributes["type"]

    if type_conversion:
        type_call = parse_type(UnknownType(type_return), caller_context)
        if caller_context.is_compact_ast:
            assert len(expression["arguments"]) == 1
            expression_to_parse = expression["arguments"][0]
        else:
            children = expression["children"]
            assert len(children) == 2
            type_info = children[0]
            expression_to_parse = children[1]
            assert type_info["name"] in [
                "ElementaryTypenameExpression",
                "ElementaryTypeNameExpression",
                "Identifier",
                "TupleExpression",
                "IndexAccess",
                "MemberAccess",
            ]

        expression = parse_expression(expression_to_parse, caller_context)
        t = TypeConversion(expression, type_call)
        t.set_offset(src, caller_context.compilation_unit)
        if isinstance(type_call, UserDefinedType):
            type_call.type.references.append(t.source_mapping)
        return t

    call_gas = None
    call_value = None
    call_salt = None
    if caller_context.is_compact_ast:
        called = parse_expression(expression["expression"], caller_context)
        # If the next expression is a FunctionCallOptions
        # We can here the gas/value information
        # This is only available if the syntax is {gas: , value: }
        # For the .gas().value(), the member are considered as function call
        # And converted later to the correct info (convert.py)
        if expression["expression"][caller_context.get_key()] == "FunctionCallOptions":
            call_with_options = expression["expression"]
            for idx, name in enumerate(call_with_options.get("names", [])):
                option = parse_expression(call_with_options["options"][idx], caller_context)
                if name == "value":
                    call_value = option
                if name == "gas":
                    call_gas = option
                if name == "salt":
                    call_salt = option
        arguments = []
        if expression["arguments"]:
            arguments = [parse_expression(a, caller_context) for a in expression["arguments"]]
    else:
        children = expression["children"]
        called = parse_expression(children[0], caller_context)
        arguments = [parse_expression(a, caller_context) for a in children[1::]]

    if isinstance(called, SuperCallExpression):
        sp = SuperCallExpression(called, arguments, type_return)
        sp.set_offset(expression["src"], caller_context.compilation_unit)
        return sp
    call_expression = CallExpression(called, arguments, type_return)
    call_expression.set_offset(src, caller_context.compilation_unit)

    # Only available if the syntax {gas:, value:} was used
    call_expression.call_gas = call_gas
    call_expression.call_value = call_value
    call_expression.call_salt = call_salt
    return call_expression


def parse_super_name(expression: Dict, is_compact_ast: bool) -> str:
    if is_compact_ast:
        assert expression["nodeType"] == "MemberAccess"
        base_name = expression["memberName"]
        arguments = expression["typeDescriptions"]["typeString"]
    else:
        assert expression["name"] == "MemberAccess"
        attributes = expression["attributes"]
        base_name = attributes["member_name"]
        arguments = attributes["type"]

    assert arguments.startswith("function ")
    # remove function (...()
    arguments = arguments[len("function ") :]

    arguments = filter_name(arguments)
    if " " in arguments:
        arguments = arguments[: arguments.find(" ")]

    return base_name + arguments


def _parse_elementary_type_name_expression(
    expression: Dict, is_compact_ast: bool, caller_context: CallerContextExpression
) -> ElementaryTypeNameExpression:
    # nop exression
    # uint;
    if is_compact_ast:
        value = expression["typeName"]
    else:
        if "children" in expression:
            value = expression["children"][0]["attributes"]["name"]
        else:
            value = expression["attributes"]["value"]
    if isinstance(value, dict):
        t = parse_type(value, caller_context)
    else:
        t = parse_type(UnknownType(value), caller_context)
    e = ElementaryTypeNameExpression(t)
    e.set_offset(expression["src"], caller_context.compilation_unit)
    return e


if TYPE_CHECKING:
    pass


def _user_defined_op_call(
    caller_context: CallerContextExpression, src, function_id: int, args: List[Any], type_call: str
) -> CallExpression:
    var, was_created = find_variable(None, caller_context, function_id)

    if was_created:
        var.set_offset(src, caller_context.compilation_unit)

    identifier = Identifier(var)
    identifier.set_offset(src, caller_context.compilation_unit)

    var.references.append(identifier.source_mapping)

    call = CallExpression(identifier, args, type_call)
    call.set_offset(src, caller_context.compilation_unit)
    return call


from slither.vyper_parsing.ast.types import Int, Call, Attribute, Name, Tuple, Hex, BinOp, Str, Assert, Compare, UnaryOp

def parse_expression(expression: Dict, caller_context) -> "Expression":
    print("parse_expression")
    print(expression, "\n")
    # assert False

    if isinstance(expression, Int):
        return Literal(str(expression.value), ElementaryType("uint256"))
    
    if isinstance(expression, Hex):
        # TODO this is an implicit conversion and could potentially be bytes20 or other?
        return Literal(str(expression.value), ElementaryType("address"))
    
    if isinstance(expression, Str):
        return Literal(str(expression.value), ElementaryType("string"))


    
    if isinstance(expression, Call):
        called = parse_expression(expression.func, caller_context)
        arguments = [parse_expression(a, caller_context) for a in expression.args]
        # Since the AST lacks the type of the return values, we recover it.
        rets = called.value.returns
        
        def get_type_str(x):
            return str(x.type)
        
        type_str = get_type_str(rets[0]) if len(rets) == 1 else f"tuple({','.join(map(get_type_str, rets))})"

        return CallExpression(called, arguments, type_str)
    
    if isinstance(expression, Attribute):
        var, was_created = find_variable(expression.attr, caller_context)
        assert var
        return Identifier(var)
    
    if isinstance(expression, Name):
        var, was_created = find_variable(expression.id, caller_context)
        print(var)
        print(var.__class__)
        assert var
        return Identifier(var)
    
    if isinstance(expression, Tuple):
        tuple_vars = [parse_expression(x, caller_context) for x in expression.elements]
        return TupleExpression(tuple_vars)
    
    if isinstance(expression, UnaryOp):
        operand = parse_expression(expression.operand, caller_context)
        op = UnaryOperationType.get_type(expression.op, isprefix=True) #TODO does vyper have postfix?

        return UnaryOperation(operand, op)

    if isinstance(expression, (BinOp, Compare)):
        lhs = parse_expression(expression.left, caller_context)
        rhs = parse_expression(expression.right, caller_context)

        op = BinaryOperationType.get_type(expression.op)
        return BinaryOperation(lhs, rhs, op)
        
    if isinstance(expression, Assert):
        type_str = "tuple()"
        if expression.msg is None:
            func = SolidityFunction("require(bool)")
            args = [parse_expression(expression.test, caller_context)]
        else:
            func = SolidityFunction("require(bool,string)")
            args = [parse_expression(expression.test, caller_context), parse_expression(expression.msg, caller_context)]

        return CallExpression(Identifier(func), args, type_str)
    
    raise ParsingError(f"Expression not parsed {expression}")
