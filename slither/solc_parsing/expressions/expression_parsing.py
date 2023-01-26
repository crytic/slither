import logging
import re
from typing import Dict, TYPE_CHECKING, Optional, Union, Callable

from slither.core.declarations import Event, Enum, Structure
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function
from slither.core.declarations.solidity_variables import (
    SOLIDITY_FUNCTIONS,
    SOLIDITY_VARIABLES,
    SOLIDITY_VARIABLES_COMPOSED,
    SolidityFunction,
    SolidityVariable,
    SolidityVariableComposed,
)
from slither.core.expressions.assignment_operation import (
    AssignmentOperation,
    AssignmentOperationType,
)
from slither.core.expressions.binary_operation import (
    BinaryOperation,
    BinaryOperationType,
)
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
from slither.core.solidity_types import (
    ArrayType,
    ElementaryType,
    FunctionType,
    MappingType,
)
from slither.solc_parsing.declarations.caller_context import CallerContextExpression
from slither.core.variables.variable import Variable
from slither.solc_parsing.exceptions import ParsingError, VariableNotFound
from slither.solc_parsing.solidity_types.type_parsing import UnknownType, parse_type
from slither.solc_parsing.ast.types import (
    Expression as ExpressionT,
    Literal as LiteralT,
    FunctionCallOptions as FunctionCallOptionsT,
    NewExpression as NewExpressionT,
    ModifierInvocation as ModifierInvocationT,
    IndexAccess as IndexAccessT,
    IndexRangeAccess as IndexRangeAccessT,
    ElementaryTypeNameExpression as ElementaryTypeNameExpressionT,
    Conditional as ConditionalT,
    TupleExpression as TupleExpressionT,
    Assignment as AssignmentT,
    UnaryOperation as UnaryOperationT,
    BinaryOperation as BinaryOperationT,
    Identifier as IdentifierT,
    MemberAccess as MemberAccessT,
    FunctionCall as FunctionCallT,
    IdentifierPath as IdentifierPathT,
    ArrayTypeName,
    ElementaryTypeName,
    UserDefinedTypeName,
)
from .find_variable import find_variable

if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression

logger = logging.getLogger("ExpressionParsing")

# pylint: disable=anomalous-backslash-in-string,import-outside-toplevel,too-many-branches,too-many-locals


def parse_super_name(expression: MemberAccessT) -> str:
    arguments = expression.type_str
    base_name = expression.member_name

    assert arguments.startswith("function ")
    # remove function (...()
    arguments = arguments[len("function ") :]

    arguments = filter_name(arguments)
    if " " in arguments:
        arguments = arguments[: arguments.find(" ")]

    return base_name + arguments


# endregion
###################################################################################
###################################################################################
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


def parse_conditional(expr: ConditionalT, ctx: CallerContextExpression) -> "Expression":
    cond = parse_expression(expr.condition, ctx)
    true_expr = parse_expression(expr.true_expr, ctx)
    false_expr = parse_expression(expr.false_expr, ctx)
    conditional = ConditionalExpression(cond, true_expr, false_expr)
    conditional.set_offset(expr.src, ctx.compilation_unit)
    return conditional


def parse_assignment(expr: AssignmentT, ctx: CallerContextExpression) -> "Expression":
    lhs = parse_expression(expr.left, ctx)
    rhs = parse_expression(expr.right, ctx)
    op = AssignmentOperationType.get_type(expr.operator)
    op_type = expr.type_str

    assignement = AssignmentOperation(lhs, rhs, op, op_type)
    assignement.set_offset(expr.src, ctx.compilation_unit)
    return assignement


def parse_tuple_expression(expr: TupleExpressionT, ctx: CallerContextExpression) -> "Expression":
    expressions = [parse_expression(e, ctx) if e else None for e in expr.components]

    t = TupleExpression(expressions)
    t.set_offset(expr.src, ctx.compilation_unit)
    return t


def parse_unary_operation(expr: UnaryOperationT, ctx: CallerContextExpression) -> "Expression":
    operation_type = UnaryOperationType.get_type(expr.operator, expr.is_prefix)
    expression = parse_expression(expr.expression, ctx)

    unary_op = UnaryOperation(expression, operation_type)
    unary_op.set_offset(expr.src, ctx.compilation_unit)
    return unary_op


def parse_binary_operation(expr: BinaryOperationT, ctx: CallerContextExpression) -> "Expression":
    operation_type = BinaryOperationType.get_type(expr.operator)
    left = parse_expression(expr.left, ctx)
    right = parse_expression(expr.right, ctx)

    binary_op = BinaryOperation(left, right, operation_type)
    binary_op.set_offset(expr.src, ctx.compilation_unit)
    return binary_op


def parse_function_call(expr: FunctionCallT, ctx: CallerContextExpression) -> "Expression":
    src = expr.src
    type_conversion = expr.kind == "typeConversion"
    type_return = expr.type_str
    if type_conversion:
        type_call = parse_type(UnknownType(type_return), ctx)
        expression_to_parse = expr.arguments[0]

        expression = parse_expression(expression_to_parse, ctx)
        t = TypeConversion(expression, type_call)
        t.set_offset(src, ctx.compilation_unit)
        return t

    call_gas = None
    call_value = None
    call_salt = None
    called = parse_expression(expr.expression, ctx)

    # If the next expression is a FunctionCallOptions
    # We can here the gas/value information
    # This is only available if the syntax is {gas: , value: }
    # For the .gas().value(), the member are considered as function call
    # And converted later to the correct info (convert.py)
    if isinstance(expr.expression, FunctionCallOptionsT):
        call_with_options = expr.expression
        for idx, name in enumerate(call_with_options.names):
            option = parse_expression(call_with_options.options[idx], ctx)
            if name == "value":
                call_value = option
            if name == "gas":
                call_gas = option
            if name == "salt":
                call_salt = option

    arguments = [parse_expression(a, ctx) for a in expr.arguments]

    if isinstance(called, SuperCallExpression):
        sp = SuperCallExpression(called, arguments, type_return)
        sp.set_offset(expr.src, ctx.compilation_unit)
        return sp
    call_expression = CallExpression(called, arguments, type_return)
    call_expression.set_offset(src, ctx.compilation_unit)

    # Only available if the syntax {gas:, value:} was used
    call_expression.call_gas = call_gas
    call_expression.call_value = call_value
    call_expression.call_salt = call_salt
    return call_expression


def parse_function_call_options(
    expr: FunctionCallOptionsT, ctx: CallerContextExpression
) -> "Expression":
    # call/gas info are handled in parse_call
    called = parse_expression(expr.expression, ctx)
    assert isinstance(called, (MemberAccess, NewContract, Identifier, TupleExpression))
    return called


def parse_new_expression(expr: NewExpressionT, ctx: CallerContextExpression) -> "Expression":
    typename = expr.typename

    if isinstance(typename, ArrayTypeName):
        depth = 0
        while isinstance(typename, ArrayTypeName):
            typename = typename.base
            depth += 1

        array_type = parse_type(typename, ctx)
        array = NewArray(depth, array_type)
        array.set_offset(expr.src, ctx.compilation_unit)
        return array
    elif isinstance(typename, ElementaryTypeName):
        new_elem = NewElementaryType(ElementaryType(typename.name))
        new_elem.set_offset(expr.src, ctx.compilation_unit)
        return new_elem
    elif isinstance(typename, UserDefinedTypeName):
        new = NewContract(typename.name)
        new.set_offset(expr.src, ctx.compilation_unit)
        return new
    else:
        raise ParsingError("unexpected new type", typename)


def parse_member_access(expr: MemberAccessT, ctx: CallerContextExpression) -> "Expression":
    member_name = expr.member_name
    member_type = expr.type_str
    member_expression = parse_expression(expr.expression, ctx)

    if str(member_expression) == "super":
        super_name = parse_super_name(expr)
        var, was_created = find_variable(super_name, ctx, is_super=True)
        if var is None:
            raise VariableNotFound(f"Super variable not found: {super_name}")
        if was_created:
            var.set_offset(expr.src, ctx.compilation_unit)
        sup = SuperIdentifier(var)
        sup.set_offset(expr.src, ctx.compilation_unit)
        return sup

    member_access = MemberAccess(member_name, member_type, member_expression)
    member_access.set_offset(expr.src, ctx.compilation_unit)
    if str(member_access) in SOLIDITY_VARIABLES_COMPOSED:
        idx = Identifier(SolidityVariableComposed(str(member_access)))
        idx.set_offset(expr.src, ctx.compilation_unit)
        return idx
    return member_access


def parse_index_access(expr: IndexAccessT, ctx: CallerContextExpression) -> "Expression":
    # IndexAccess is used to describe ElementaryTypeNameExpression
    # if abi.decode is used
    # For example, abi.decode(data, ...(uint[]) )
    if expr.index is None:
        ret = parse_expression(expr.base, ctx)
        # Nested array are not yet available in abi.decode
        if isinstance(ret, ElementaryTypeNameExpression):
            old_type = ret.type
            ret.type = ArrayType(old_type, None)
        return ret

    left_expression = parse_expression(expr.base, ctx)
    right_expression = parse_expression(expr.index, ctx)
    index = IndexAccess(left_expression, right_expression, expr.type_str)
    index.set_offset(expr.src, ctx.compilation_unit)
    return index


def parse_index_range_access(expr: IndexRangeAccessT, ctx: CallerContextExpression) -> "Expression":
    # For now, we convert array slices to a direct array access
    # As a result the generated IR will lose the slices information
    # As far as I understand, array slice are only used in abi.decode
    # https://solidity.readthedocs.io/en/v0.6.12/types.html
    # TODO: Investigate array slices usage and implication for the IR
    return parse_expression(expr.base, ctx)


def parse_identifier(expr: IdentifierT, ctx: CallerContextExpression) -> "Expression":
    value = expr.name
    t = expr.type_str

    if t:
        found = re.findall("[struct|enum|function|modifier] \(([\[\] ()a-zA-Z0-9\.,_]*)\)", t)
        assert len(found) <= 1
        if found:
            value = value + "(" + found[0] + ")"
            value = filter_name(value)

    var, was_created = find_variable(value, ctx, expr.referenced_declaration)
    if was_created:
        var.set_offset(expr.src, ctx.compilation_unit)

    identifier = Identifier(var)
    identifier.set_offset(expr.src, ctx.compilation_unit)
    return identifier


def parse_elementary_type_name_expression(
    expr: ElementaryTypeNameExpressionT, ctx: CallerContextExpression
) -> "Expression":
    t = parse_type(expr.typename, ctx)
    e = ElementaryTypeNameExpression(t)
    e.set_offset(expr.src, ctx.compilation_unit)
    return e


def parse_literal(expr: LiteralT, ctx: CallerContextExpression) -> "Expression":
    subdenomination = None

    value = expr.value
    if value:
        subdenomination = expr.subdenomination
    elif not value and value != "":
        value = "0x" + expr.hex_value
    type_candidate = expr.type_str

    # Length declaration for array was None until solc 0.5.5
    if type_candidate is None:
        if expr.kind == "number":
            type_candidate = "int_const"

    if type_candidate is None:
        if value.isdecimal():
            type_candidate = ElementaryType("uint256")
        else:
            type_candidate = ElementaryType("string")
    elif type_candidate.startswith("int_const "):
        type_candidate = ElementaryType("uint256")
    elif type_candidate.startswith("bool"):
        type_candidate = ElementaryType("bool")
    elif type_candidate.startswith("address"):
        type_candidate = ElementaryType("address")
    else:
        type_candidate = ElementaryType("string")
    literal = Literal(value, type_candidate, subdenomination)
    literal.set_offset(expr.src, ctx.compilation_unit)
    return literal


def parse_modifier_invocation(
    expr: ModifierInvocationT, ctx: CallerContextExpression
) -> "Expression":
    called = parse_expression(expr.modifier, ctx)
    args = [parse_expression(a, ctx) for a in expr.args] if expr.args else []

    call = CallExpression(called, args, "Modifier")
    call.set_offset(expr.src, ctx.compilation_unit)
    return call


def parse_identifier_path(expr: IdentifierPathT, ctx: CallerContextExpression) -> "Expression":
    var, was_created = find_variable(
        expr.name, ctx, expr.referenced_declaration, is_identifier_path=True
    )
    if was_created:
        var.set_offset(expr.src, ctx.compilation_unit)

    identifier = Identifier(var)
    identifier.set_offset(expr.src, ctx.compilation_unit)

    var.references.append(identifier.source_mapping)

    return identifier


def parse_unhandled(expr: ExpressionT, ctx: CallerContextExpression) -> "Expression":
    raise Exception("unhandled expr", type(expr))


def parse_expression(expr: ExpressionT, ctx: CallerContextExpression) -> "Expression":
    return PARSERS.get(type(expr), parse_unhandled)(expr, ctx)


PARSERS: Dict[type, Callable[[ExpressionT], "Expression"]] = {
    ConditionalT: parse_conditional,
    AssignmentT: parse_assignment,
    TupleExpressionT: parse_tuple_expression,
    UnaryOperationT: parse_unary_operation,
    BinaryOperationT: parse_binary_operation,
    FunctionCallT: parse_function_call,
    FunctionCallOptionsT: parse_function_call_options,
    NewExpressionT: parse_new_expression,
    MemberAccessT: parse_member_access,
    IndexAccessT: parse_index_access,
    IndexRangeAccessT: parse_index_range_access,
    IdentifierT: parse_identifier,
    ElementaryTypeNameExpressionT: parse_elementary_type_name_expression,
    LiteralT: parse_literal,
    IdentifierPathT: parse_identifier_path,
    ModifierInvocationT: parse_modifier_invocation,
}
# endregion
