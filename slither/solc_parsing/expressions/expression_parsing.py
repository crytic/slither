import logging
import re
from typing import Dict, TYPE_CHECKING, Optional, Union

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
from slither.core.expressions.binary_operation import BinaryOperation, BinaryOperationType
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
from slither.core.solidity_types import ArrayType, ElementaryType, FunctionType, MappingType
from slither.core.variables.variable import Variable
from slither.solc_parsing.exceptions import ParsingError, VariableNotFound
from slither.solc_parsing.solidity_types.type_parsing import UnknownType, parse_type

if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression
    from slither.solc_parsing.declarations.function import FunctionSolc
    from slither.solc_parsing.declarations.contract import ContractSolc

logger = logging.getLogger("ExpressionParsing")

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


def find_variable(
    var_name: str,
    caller_context: CallerContext,
    referenced_declaration: Optional[int] = None,
    is_super=False,
) -> Union[
    Variable, Function, Contract, SolidityVariable, SolidityFunction, Event, Enum, Structure
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


def parse_call(expression: Dict, caller_context):
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
        t.set_offset(src, caller_context.slither)
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
        sp.set_offset(expression["src"], caller_context.slither)
        return sp
    call_expression = CallExpression(called, arguments, type_return)
    call_expression.set_offset(src, caller_context.slither)

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
    expression: Dict, is_compact_ast: bool, caller_context
) -> ElementaryTypeNameExpression:
    # nop exression
    # uint;
    if is_compact_ast:
        value = expression["typeName"]
    else:
        assert "children" not in expression
        value = expression["attributes"]["value"]
    if isinstance(value, dict):
        t = parse_type(value, caller_context)
    else:
        t = parse_type(UnknownType(value), caller_context)
    e = ElementaryTypeNameExpression(t)
    e.set_offset(expression["src"], caller_context.slither)
    return e


def parse_expression(expression: Dict, caller_context: CallerContext) -> "Expression":
    """

    Returns:
        str: expression
    """
    #  Expression
    #    = Expression ('++' | '--')
    #    | NewExpression
    #    | IndexAccess
    #    | MemberAccess
    #    | FunctionCall
    #    | '(' Expression ')'
    #    | ('!' | '~' | 'delete' | '++' | '--' | '+' | '-') Expression
    #    | Expression '**' Expression
    #    | Expression ('*' | '/' | '%') Expression
    #    | Expression ('+' | '-') Expression
    #    | Expression ('<<' | '>>') Expression
    #    | Expression '&' Expression
    #    | Expression '^' Expression
    #    | Expression '|' Expression
    #    | Expression ('<' | '>' | '<=' | '>=') Expression
    #    | Expression ('==' | '!=') Expression
    #    | Expression '&&' Expression
    #    | Expression '||' Expression
    #    | Expression '?' Expression ':' Expression
    #    | Expression ('=' | '|=' | '^=' | '&=' | '<<=' | '>>=' | '+=' | '-=' | '*=' | '/=' | '%=') Expression
    #    | PrimaryExpression
    # The AST naming does not follow the spec
    name = expression[caller_context.get_key()]
    is_compact_ast = caller_context.is_compact_ast
    src = expression["src"]

    if name == "UnaryOperation":
        if is_compact_ast:
            attributes = expression
        else:
            attributes = expression["attributes"]
        assert "prefix" in attributes
        operation_type = UnaryOperationType.get_type(attributes["operator"], attributes["prefix"])

        if is_compact_ast:
            expression = parse_expression(expression["subExpression"], caller_context)
        else:
            assert len(expression["children"]) == 1
            expression = parse_expression(expression["children"][0], caller_context)
        unary_op = UnaryOperation(expression, operation_type)
        unary_op.set_offset(src, caller_context.slither)
        return unary_op

    elif name == "BinaryOperation":
        if is_compact_ast:
            attributes = expression
        else:
            attributes = expression["attributes"]
        operation_type = BinaryOperationType.get_type(attributes["operator"])

        if is_compact_ast:
            left_expression = parse_expression(expression["leftExpression"], caller_context)
            right_expression = parse_expression(expression["rightExpression"], caller_context)
        else:
            assert len(expression["children"]) == 2
            left_expression = parse_expression(expression["children"][0], caller_context)
            right_expression = parse_expression(expression["children"][1], caller_context)
        binary_op = BinaryOperation(left_expression, right_expression, operation_type)
        binary_op.set_offset(src, caller_context.slither)
        return binary_op

    elif name in "FunctionCall":
        return parse_call(expression, caller_context)

    elif name == "FunctionCallOptions":
        # call/gas info are handled in parse_call
        called = parse_expression(expression["expression"], caller_context)
        assert isinstance(called, (MemberAccess, NewContract))
        return called

    elif name == "TupleExpression":
        """
            For expression like
            (a,,c) = (1,2,3)
            the AST provides only two children in the left side
            We check the type provided (tuple(uint256,,uint256))
            To determine that there is an empty variable
            Otherwhise we would not be able to determine that
            a = 1, c = 3, and 2 is lost

            Note: this is only possible with Solidity >= 0.4.12
        """
        if is_compact_ast:
            expressions = [
                parse_expression(e, caller_context) if e else None for e in expression["components"]
            ]
        else:
            if "children" not in expression:
                attributes = expression["attributes"]
                components = attributes["components"]
                expressions = [
                    parse_expression(c, caller_context) if c else None for c in components
                ]
            else:
                expressions = [parse_expression(e, caller_context) for e in expression["children"]]
        # Add none for empty tuple items
        if "attributes" in expression:
            if "type" in expression["attributes"]:
                t = expression["attributes"]["type"]
                if ",," in t or "(," in t or ",)" in t:
                    t = t[len("tuple(") : -1]
                    elems = t.split(",")
                    for idx in range(len(elems)):
                        if elems[idx] == "":
                            expressions.insert(idx, None)
        t = TupleExpression(expressions)
        t.set_offset(src, caller_context.slither)
        return t

    elif name == "Conditional":
        if is_compact_ast:
            if_expression = parse_expression(expression["condition"], caller_context)
            then_expression = parse_expression(expression["trueExpression"], caller_context)
            else_expression = parse_expression(expression["falseExpression"], caller_context)
        else:
            children = expression["children"]
            assert len(children) == 3
            if_expression = parse_expression(children[0], caller_context)
            then_expression = parse_expression(children[1], caller_context)
            else_expression = parse_expression(children[2], caller_context)
        conditional = ConditionalExpression(if_expression, then_expression, else_expression)
        conditional.set_offset(src, caller_context.slither)
        return conditional

    elif name == "Assignment":
        if is_compact_ast:
            left_expression = parse_expression(expression["leftHandSide"], caller_context)
            right_expression = parse_expression(expression["rightHandSide"], caller_context)

            operation_type = AssignmentOperationType.get_type(expression["operator"])

            operation_return_type = expression["typeDescriptions"]["typeString"]
        else:
            attributes = expression["attributes"]
            children = expression["children"]
            assert len(expression["children"]) == 2
            left_expression = parse_expression(children[0], caller_context)
            right_expression = parse_expression(children[1], caller_context)

            operation_type = AssignmentOperationType.get_type(attributes["operator"])
            operation_return_type = attributes["type"]

        assignement = AssignmentOperation(
            left_expression, right_expression, operation_type, operation_return_type
        )
        assignement.set_offset(src, caller_context.slither)
        return assignement

    elif name == "Literal":

        subdenomination = None

        assert "children" not in expression

        if is_compact_ast:
            value = expression["value"]
            if value:
                if "subdenomination" in expression and expression["subdenomination"]:
                    subdenomination = expression["subdenomination"]
            elif not value and value != "":
                value = "0x" + expression["hexValue"]
            type_candidate = expression["typeDescriptions"]["typeString"]

            # Length declaration for array was None until solc 0.5.5
            if type_candidate is None:
                if expression["kind"] == "number":
                    type_candidate = "int_const"
        else:
            value = expression["attributes"]["value"]
            if value:
                if (
                    "subdenomination" in expression["attributes"]
                    and expression["attributes"]["subdenomination"]
                ):
                    subdenomination = expression["attributes"]["subdenomination"]
            elif value is None:
                # for literal declared as hex
                # see https://solidity.readthedocs.io/en/v0.4.25/types.html?highlight=hex#hexadecimal-literals
                assert "hexvalue" in expression["attributes"]
                value = "0x" + expression["attributes"]["hexvalue"]
            type_candidate = expression["attributes"]["type"]

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
        literal.set_offset(src, caller_context.slither)
        return literal

    elif name == "Identifier":
        assert "children" not in expression

        t = None

        if caller_context.is_compact_ast:
            value = expression["name"]
            t = expression["typeDescriptions"]["typeString"]
        else:
            value = expression["attributes"]["value"]
            if "type" in expression["attributes"]:
                t = expression["attributes"]["type"]

        if t:
            found = re.findall("[struct|enum|function|modifier] \(([\[\] ()a-zA-Z0-9\.,_]*)\)", t)
            assert len(found) <= 1
            if found:
                value = value + "(" + found[0] + ")"
                value = filter_name(value)

        if "referencedDeclaration" in expression:
            referenced_declaration = expression["referencedDeclaration"]
        else:
            referenced_declaration = None

        var = find_variable(value, caller_context, referenced_declaration)

        identifier = Identifier(var)
        identifier.set_offset(src, caller_context.slither)
        return identifier

    elif name == "IndexAccess":
        if is_compact_ast:
            index_type = expression["typeDescriptions"]["typeString"]
            left = expression["baseExpression"]
            right = expression["indexExpression"]
        else:
            index_type = expression["attributes"]["type"]
            children = expression["children"]
            assert len(children) == 2
            left = children[0]
            right = children[1]
        # IndexAccess is used to describe ElementaryTypeNameExpression
        # if abi.decode is used
        # For example, abi.decode(data, ...(uint[]) )
        if right is None:
            ret = parse_expression(left, caller_context)
            # Nested array are not yet available in abi.decode
            if isinstance(ret, ElementaryTypeNameExpression):
                old_type = ret.type
                ret.type = ArrayType(old_type, None)
            return ret

        left_expression = parse_expression(left, caller_context)
        right_expression = parse_expression(right, caller_context)
        index = IndexAccess(left_expression, right_expression, index_type)
        index.set_offset(src, caller_context.slither)
        return index

    elif name == "MemberAccess":
        if caller_context.is_compact_ast:
            member_name = expression["memberName"]
            member_type = expression["typeDescriptions"]["typeString"]
            member_expression = parse_expression(expression["expression"], caller_context)
        else:
            member_name = expression["attributes"]["member_name"]
            member_type = expression["attributes"]["type"]
            children = expression["children"]
            assert len(children) == 1
            member_expression = parse_expression(children[0], caller_context)
        if str(member_expression) == "super":
            super_name = parse_super_name(expression, is_compact_ast)
            var = find_variable(super_name, caller_context, is_super=True)
            if var is None:
                raise VariableNotFound("Variable not found: {}".format(super_name))
            sup = SuperIdentifier(var)
            sup.set_offset(src, caller_context.slither)
            return sup
        member_access = MemberAccess(member_name, member_type, member_expression)
        member_access.set_offset(src, caller_context.slither)
        if str(member_access) in SOLIDITY_VARIABLES_COMPOSED:
            idx = Identifier(SolidityVariableComposed(str(member_access)))
            idx.set_offset(src, caller_context.slither)
            return idx
        return member_access

    elif name == "ElementaryTypeNameExpression":
        return _parse_elementary_type_name_expression(expression, is_compact_ast, caller_context)

    # NewExpression is not a root expression, it's always the child of another expression
    elif name == "NewExpression":

        if is_compact_ast:
            type_name = expression["typeName"]
        else:
            children = expression["children"]
            assert len(children) == 1
            type_name = children[0]

        if type_name[caller_context.get_key()] == "ArrayTypeName":
            depth = 0
            while type_name[caller_context.get_key()] == "ArrayTypeName":
                # Note: dont conserve the size of the array if provided
                # We compute it directly
                if is_compact_ast:
                    type_name = type_name["baseType"]
                else:
                    type_name = type_name["children"][0]
                depth += 1
            if type_name[caller_context.get_key()] == "ElementaryTypeName":
                if is_compact_ast:
                    array_type = ElementaryType(type_name["name"])
                else:
                    array_type = ElementaryType(type_name["attributes"]["name"])
            elif type_name[caller_context.get_key()] == "UserDefinedTypeName":
                if is_compact_ast:
                    array_type = parse_type(UnknownType(type_name["name"]), caller_context)
                else:
                    array_type = parse_type(
                        UnknownType(type_name["attributes"]["name"]), caller_context
                    )
            elif type_name[caller_context.get_key()] == "FunctionTypeName":
                array_type = parse_type(type_name, caller_context)
            else:
                raise ParsingError("Incorrect type array {}".format(type_name))
            array = NewArray(depth, array_type)
            array.set_offset(src, caller_context.slither)
            return array

        if type_name[caller_context.get_key()] == "ElementaryTypeName":
            if is_compact_ast:
                elem_type = ElementaryType(type_name["name"])
            else:
                elem_type = ElementaryType(type_name["attributes"]["name"])
            new_elem = NewElementaryType(elem_type)
            new_elem.set_offset(src, caller_context.slither)
            return new_elem

        assert type_name[caller_context.get_key()] == "UserDefinedTypeName"

        if is_compact_ast:
            contract_name = type_name["name"]
        else:
            contract_name = type_name["attributes"]["name"]
        new = NewContract(contract_name)
        new.set_offset(src, caller_context.slither)
        return new

    elif name == "ModifierInvocation":

        if is_compact_ast:
            called = parse_expression(expression["modifierName"], caller_context)
            arguments = []
            if expression["arguments"]:
                arguments = [parse_expression(a, caller_context) for a in expression["arguments"]]
        else:
            children = expression["children"]
            called = parse_expression(children[0], caller_context)
            arguments = [parse_expression(a, caller_context) for a in children[1::]]

        call = CallExpression(called, arguments, "Modifier")
        call.set_offset(src, caller_context.slither)
        return call

    elif name == "IndexRangeAccess":
        # For now, we convert array slices to a direct array access
        # As a result the generated IR will lose the slices information
        # As far as I understand, array slice are only used in abi.decode
        # https://solidity.readthedocs.io/en/v0.6.12/types.html
        # TODO: Investigate array slices usage and implication for the IR
        base = parse_expression(expression["baseExpression"], caller_context)
        return base

    raise ParsingError("Expression not parsed %s" % name)
