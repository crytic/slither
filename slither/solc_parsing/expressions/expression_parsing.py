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
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.conditional_expression import ConditionalExpression
from slither.core.expressions.elementary_type_name_expression import ElementaryTypeNameExpression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.index_access import IndexAccess
from slither.core.expressions.literal import Literal
from slither.core.expressions.member_access import MemberAccess
from slither.core.expressions.new_array import NewArray
from slither.core.expressions.new_contract import NewContract
from slither.core.expressions.new_elementary_type import NewElementaryType
from slither.core.expressions.super_call_expression import SuperCallExpression
from slither.core.expressions.super_identifier import SuperIdentifier
from slither.core.expressions.tuple_expression import TupleExpression
from slither.core.expressions.type_conversion import TypeConversion
from slither.core.expressions.unary_operation import UnaryOperation, UnaryOperationType
from slither.core.solidity_types import (
    ArrayType,
    ElementaryType,
    FunctionType,
    MappingType,
)
from slither.core.variables.variable import Variable
from slither.solc_parsing.exceptions import ParsingError, VariableNotFound
from slither.solc_parsing.solidity_types.type_parsing import parse_type
from slither.solc_parsing.types.types import \
    Expression as ExpressionT, \
    Literal as LiteralT, \
    FunctionCallOptions as FunctionCallOptionsT, \
    NewExpression as NewExpressionT, \
    ModifierInvocation as ModifierInvocationT, \
    IndexAccess as IndexAccessT, \
    IndexRangeAccess as IndexRangeAccessT, \
    ElementaryTypeNameExpression as ElementaryTypeNameExpressionT, \
    Conditional as ConditionalT, \
    TupleExpression as TupleExpressionT, \
    Assignment as AssignmentT, \
    UnaryOperation as UnaryOperationT, \
    BinaryOperation as BinaryOperationT, \
    Identifier as IdentifierT, \
    MemberAccess as MemberAccessT, \
    FunctionCall as FunctionCallT, ArrayTypeName, ElementaryTypeName, UserDefinedTypeName

if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression
    from slither.solc_parsing.declarations.function import FunctionSolc
    from slither.solc_parsing.declarations.contract import ContractSolc

logger = logging.getLogger("ExpressionParsing")

# pylint: disable=anomalous-backslash-in-string,import-outside-toplevel,too-many-branches,too-many-locals

###################################################################################
###################################################################################
# region Helpers
###################################################################################
###################################################################################

CallerContext = Union["ContractSolc", "FunctionSolc"]


def get_pointer_name(variable: Variable):
    curr_type = variable.type
    while isinstance(curr_type, (ArrayType, MappingType)):
        if isinstance(curr_type, ArrayType):
            curr_type = curr_type.type
        else:
            assert isinstance(curr_type, MappingType)
            curr_type = curr_type.type_to

    if isinstance(curr_type, FunctionType):
        return variable.name + curr_type.parameters_signature
    return None


def find_variable(  # pylint: disable=too-many-locals,too-many-statements
    var_name: str,
    caller_context: CallerContext,
    referenced_declaration: Optional[int] = None,
    is_super=False,
) -> Union[
    Variable,
    Function,
    Contract,
    SolidityVariable,
    SolidityFunction,
    Event,
    Enum,
    Structure,
]:
    from slither.solc_parsing.declarations.contract import ContractSolc
    from slither.solc_parsing.declarations.function import FunctionSolc

    # variable are looked from the contract declarer
    # functions can be shadowed, but are looked from the contract instance, rather than the contract declarer
    # the difference between function and variable come from the fact that an internal call, or an variable access
    # in a function does not behave similariy, for example in:
    # contract C{
    #   function f(){
    #     state_var = 1
    #     f2()
    #  }
    # state_var will refer to C.state_var, no mater if C is inherited
    # while f2() will refer to the function definition of the inherited contract (C.f2() in the context of C, or
    # the contract inheriting from C)
    # for events it's unclear what should be the behavior, as they can be shadowed, but there is not impact
    # structure/enums cannot be shadowed

    if isinstance(caller_context, ContractSolc):
        function: Optional[FunctionSolc] = None
        contract = caller_context.underlying_contract
        contract_declarer = caller_context.underlying_contract
    elif isinstance(caller_context, FunctionSolc):
        function = caller_context
        contract = function.underlying_function.contract
        contract_declarer = function.underlying_function.contract_declarer
    else:
        raise ParsingError("Incorrect caller context")

    if function:
        # We look for variable declared with the referencedDeclaration attr
        func_variables = function.variables_renamed
        if referenced_declaration and referenced_declaration in func_variables:
            return func_variables[referenced_declaration].underlying_variable
        # If not found, check for name
        func_variables = function.underlying_function.variables_as_dict
        if var_name in func_variables:
            return func_variables[var_name]
        # A local variable can be a pointer
        # for example
        # function test(function(uint) internal returns(bool) t) interna{
        # Will have a local variable t which will match the signature
        # t(uint256)
        func_variables_ptr = {
            get_pointer_name(f): f for f in function.underlying_function.variables
        }
        if var_name and var_name in func_variables_ptr:
            return func_variables_ptr[var_name]

    # variable are looked from the contract declarer
    contract_variables = contract_declarer.variables_as_dict
    if var_name in contract_variables:
        return contract_variables[var_name]

    # A state variable can be a pointer
    conc_variables_ptr = {get_pointer_name(f): f for f in contract_declarer.variables}
    if var_name and var_name in conc_variables_ptr:
        return conc_variables_ptr[var_name]

    if is_super:
        getter_available = lambda f: f.functions_declared
        d = {f.canonical_name: f for f in contract.functions}
        functions = {
            f.full_name: f
            for f in contract_declarer.available_elements_from_inheritances(
                d, getter_available
            ).values()
        }
    else:
        functions = contract.available_functions_as_dict()
    if var_name in functions:
        return functions[var_name]

    if is_super:
        getter_available = lambda m: m.modifiers_declared
        d = {m.canonical_name: m for m in contract.modifiers}
        modifiers = {
            m.full_name: m
            for m in contract_declarer.available_elements_from_inheritances(
                d, getter_available
            ).values()
        }
    else:
        modifiers = contract.available_modifiers_as_dict()
    if var_name in modifiers:
        return modifiers[var_name]

    # structures are looked on the contract declarer
    structures = contract.structures_as_dict
    if var_name in structures:
        return structures[var_name]

    structures_top_level = contract.slither.top_level_structures
    for st in structures_top_level:
        if st.name == var_name:
            return st

    events = contract.events_as_dict
    if var_name in events:
        return events[var_name]

    enums = contract.enums_as_dict
    if var_name in enums:
        return enums[var_name]

    enums_top_level = contract.slither.top_level_enums
    for enum in enums_top_level:
        if enum.name == var_name:
            return enum

    # If the enum is refered as its name rather than its canonicalName
    enums = {e.name: e for e in contract.enums}
    if var_name in enums:
        return enums[var_name]

    # Could refer to any enum
    all_enums = [c.enums_as_dict for c in contract.slither.contracts]
    all_enums = {k: v for d in all_enums for k, v in d.items()}
    if var_name in all_enums:
        return all_enums[var_name]

    if var_name in SOLIDITY_VARIABLES:
        return SolidityVariable(var_name)

    if var_name in SOLIDITY_FUNCTIONS:
        return SolidityFunction(var_name)

    contracts = contract.slither.contracts_as_dict
    if var_name in contracts:
        return contracts[var_name]

    if referenced_declaration:
        # id of the contracts is the referenced declaration
        # This is not true for the functions, as we dont always have the referenced_declaration
        # But maybe we could? (TODO)
        for contract_candidate in contract.slither.contracts:
            if contract_candidate.id == referenced_declaration:
                return contract_candidate
        for function_candidate in caller_context.slither_parser.all_functions_parser:
            if function_candidate.referenced_declaration == referenced_declaration:
                return function_candidate.underlying_function

    raise VariableNotFound("Variable not found: {} (context {})".format(var_name, caller_context))


def parse_super_name(expression: MemberAccessT) -> str:
    arguments = expression.type_str
    base_name = expression.member_name

    assert arguments.startswith("function ")
    # remove function (...()
    arguments = arguments[len("function "):]

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


def parse_conditional(expr: ConditionalT, ctx: CallerContext) -> "Expression":
    cond = parse_expression(expr.condition, ctx)
    true_expr = parse_expression(expr.true_expr, ctx)
    false_expr = parse_expression(expr.false_expr, ctx)
    conditional = ConditionalExpression(cond, true_expr, false_expr)
    conditional.set_offset(expr.src, ctx.slither)
    return conditional


def parse_assignment(expr: AssignmentT, ctx: CallerContext) -> "Expression":
    lhs = parse_expression(expr.left, ctx)
    rhs = parse_expression(expr.right, ctx)
    op = AssignmentOperationType.get_type(expr.operator)
    op_type = expr.type_str

    assignement = AssignmentOperation(lhs, rhs, op, op_type)
    assignement.set_offset(expr.src, ctx.slither)
    return assignement


def parse_tuple_expression(expr: TupleExpressionT, ctx: CallerContext) -> "Expression":
    expressions = [parse_expression(e, ctx) if e else None for e in expr.components]

    t = TupleExpression(expressions)
    t.set_offset(expr.src, ctx.slither)
    return t


def parse_unary_operation(expr: UnaryOperationT, ctx: CallerContext) -> "Expression":
    operation_type = UnaryOperationType.get_type(expr.operator, expr.is_prefix)
    expression = parse_expression(expr.expression, ctx)

    unary_op = UnaryOperation(expression, operation_type)
    unary_op.set_offset(expr.src, ctx.slither)
    return unary_op


def parse_binary_operation(expr: BinaryOperationT, ctx: CallerContext) -> "Expression":
    operation_type = BinaryOperationType.get_type(expr.operator)
    left = parse_expression(expr.left, ctx)
    right = parse_expression(expr.right, ctx)

    binary_op = BinaryOperation(left, right, operation_type)
    binary_op.set_offset(expr.src, ctx.slither)
    return binary_op


def parse_function_call(expr: FunctionCallT, ctx: CallerContext) -> "Expression":
    src = expr.src
    type_conversion = expr.kind == "typeConversion"
    type_return = expr.type_str

    if type_conversion:
        type_call = parse_type(type_return, ctx)
        expression_to_parse = expr.arguments[0]

        expression = parse_expression(expression_to_parse, ctx)
        t = TypeConversion(expression, type_call)
        t.set_offset(src, ctx.slither)
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
        sp.set_offset(expr.src, ctx.slither)
        return sp
    call_expression = CallExpression(called, arguments, type_return)
    call_expression.set_offset(src, ctx.slither)

    # Only available if the syntax {gas:, value:} was used
    call_expression.call_gas = call_gas
    call_expression.call_value = call_value
    call_expression.call_salt = call_salt
    return call_expression


def parse_function_call_options(expr: FunctionCallOptionsT, ctx: CallerContext) -> "Expression":
    # call/gas info are handled in parse_call
    called = parse_expression(expr.expression, ctx)
    assert isinstance(called, (MemberAccess, NewContract))
    return called


def parse_new_expression(expr: NewExpressionT, ctx: CallerContext) -> "Expression":
    typename = expr.typename

    if isinstance(typename, ArrayTypeName):
        depth = 0
        while isinstance(typename, ArrayTypeName):
            typename = typename.base
            depth += 1

        array_type = parse_type(typename, ctx)
        array = NewArray(depth, array_type)
        array.set_offset(expr.src, ctx.slither)
        return array
    elif isinstance(typename, ElementaryTypeName):
        new_elem = NewElementaryType(typename.name)
        new_elem.set_offset(expr.src, ctx.slither)
        return new_elem
    elif isinstance(typename, UserDefinedTypeName):
        new = NewContract(typename.name)
        new.set_offset(expr.src, ctx.slither)
        return new
    else:
        raise ParsingError("unexpected new type", typename)


def parse_member_access(expr: MemberAccessT, ctx: CallerContext) -> "Expression":
    member_name = expr.member_name
    member_type = expr.type_str
    member_expression = parse_expression(expr.expression, ctx)

    if str(member_expression) == "super":
        super_name = parse_super_name(expr)
        var = find_variable(super_name, ctx, is_super=True)
        if var is None:
            raise VariableNotFound("Variable not found: {}".format(super_name))
        sup = SuperIdentifier(var)
        sup.set_offset(expr.src, ctx.slither)
        return sup

    member_access = MemberAccess(member_name, member_type, member_expression)
    member_access.set_offset(expr.src, ctx.slither)
    if str(member_access) in SOLIDITY_VARIABLES_COMPOSED:
        idx = Identifier(SolidityVariableComposed(str(member_access)))
        idx.set_offset(expr.src, ctx.slither)
        return idx
    return member_access


def parse_index_access(expr: IndexAccessT, ctx: CallerContext) -> "Expression":
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
    index.set_offset(expr.src, ctx.slither)
    return index


def parse_index_range_access(expr: IndexRangeAccessT, ctx: CallerContext) -> "Expression":
    # For now, we convert array slices to a direct array access
    # As a result the generated IR will lose the slices information
    # As far as I understand, array slice are only used in abi.decode
    # https://solidity.readthedocs.io/en/v0.6.12/types.html
    # TODO: Investigate array slices usage and implication for the IR
    return parse_expression(expr.base, ctx)


def parse_identifier(expr: IdentifierT, ctx: CallerContext) -> "Expression":
    value = expr.name
    t = expr.type_str

    if t:
        found = re.findall("[struct|enum|function|modifier] \(([\[\] ()a-zA-Z0-9\.,_]*)\)", t)
        assert len(found) <= 1
        if found:
            value = value + "(" + found[0] + ")"
            value = filter_name(value)

    referenced_declaration = None  # expr.referenced_declaration

    var = find_variable(value, ctx, referenced_declaration)

    identifier = Identifier(var)
    identifier.set_offset(expr.src, ctx.slither)
    return identifier


def parse_elementary_type_name_expression(expr: ElementaryTypeNameExpressionT, ctx: CallerContext) -> "Expression":
    t = parse_type(expr.typename, ctx)
    e = ElementaryTypeNameExpression(t)
    e.set_offset(expr.src, ctx.slither)
    return e

def parse_literal(expr: LiteralT, ctx: CallerContext) -> "Expression":
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
    literal.set_offset(expr.src, ctx.slither)
    return literal

def parse_modifier_invocation(expr: ModifierInvocationT, ctx: CallerContext) -> "Expression":
    called = parse_expression(expr.modifier, ctx)
    args = [parse_expression(a, ctx) for a in expr.args] if expr.args else []

    call = CallExpression(called, args, "Modifier")
    call.set_offset(expr.src, ctx.slither)
    return call


def parse_unhandled(expr: ExpressionT, ctx: CallerContext) -> "Expression":
    raise Exception("unhandled expr", type(expr))


def parse_expression(expr: ExpressionT, ctx: CallerContext) -> "Expression":
    return PARSERS.get(type(expr), parse_unhandled)(expr, ctx)


PARSERS: Dict[type, Callable[[ExpressionT, CallerContext], "Expression"]] = {
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

    ModifierInvocationT: parse_modifier_invocation,
}
# endregion
