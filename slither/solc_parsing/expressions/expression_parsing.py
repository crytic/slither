import logging
import re
from typing import Dict, TYPE_CHECKING

from slither.core.declarations.solidity_variables import (
    SOLIDITY_VARIABLES_COMPOSED,
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
)
from slither.solc_parsing.declarations.caller_context import CallerContextExpression
from slither.solc_parsing.exceptions import ParsingError, VariableNotFound
from slither.solc_parsing.expressions.find_variable import find_variable
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


def parse_call(expression: Dict, caller_context):  # pylint: disable=too-many-statements
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

    from slither.core.scope.scope import FileScope


def parse_expression(expression: Dict, caller_context: CallerContextExpression) -> "Expression":
    # pylint: disable=too-many-nested-blocks,too-many-statements
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
    assert isinstance(caller_context, CallerContextExpression)
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
        unary_op.set_offset(src, caller_context.compilation_unit)
        return unary_op

    if name == "BinaryOperation":
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
        binary_op.set_offset(src, caller_context.compilation_unit)
        return binary_op

    if name in "FunctionCall":
        return parse_call(expression, caller_context)

    if name == "FunctionCallOptions":
        # call/gas info are handled in parse_call
        if is_compact_ast:
            called = parse_expression(expression["expression"], caller_context)
        else:
            called = parse_expression(expression["children"][0], caller_context)
        assert isinstance(called, (MemberAccess, NewContract, Identifier, TupleExpression))
        return called

    if name == "TupleExpression":
        #     For expression like
        #     (a,,c) = (1,2,3)
        #     the AST provides only two children in the left side
        #     We check the type provided (tuple(uint256,,uint256))
        #     To determine that there is an empty variable
        #     Otherwhise we would not be able to determine that
        #     a = 1, c = 3, and 2 is lost
        #
        #     Note: this is only possible with Solidity >= 0.4.12
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
                    for idx, _ in enumerate(elems):
                        if elems[idx] == "":
                            expressions.insert(idx, None)
        t = TupleExpression(expressions)
        t.set_offset(src, caller_context.compilation_unit)
        return t

    if name == "Conditional":
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
        conditional.set_offset(src, caller_context.compilation_unit)
        return conditional

    if name == "Assignment":
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
        assignement.set_offset(src, caller_context.compilation_unit)
        return assignement

    if name == "Literal":

        subdenomination = None

        assert "children" not in expression

        if is_compact_ast:
            value = expression.get("value", None)
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
            value = expression["attributes"].get("value", None)
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
        literal.set_offset(src, caller_context.compilation_unit)
        return literal

    if name == "Identifier":
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

        var, was_created = find_variable(value, caller_context, referenced_declaration)
        if was_created:
            var.set_offset(src, caller_context.compilation_unit)

        identifier = Identifier(var)
        identifier.set_offset(src, caller_context.compilation_unit)
        return identifier

    if name == "IndexAccess":
        if is_compact_ast:
            index_type = expression["typeDescriptions"]["typeString"]
            left = expression["baseExpression"]
            right = expression.get("indexExpression", None)
        else:
            index_type = expression["attributes"]["type"]
            children = expression["children"]
            left = children[0]
            right = children[1] if len(children) > 1 else None
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
        index.set_offset(src, caller_context.compilation_unit)
        return index

    if name == "MemberAccess":
        if caller_context.is_compact_ast:
            member_name = expression["memberName"]
            member_type = expression["typeDescriptions"]["typeString"]
            # member_type = parse_type(
            #     UnknownType(expression["typeDescriptions"]["typeString"]), caller_context
            # )
            member_expression = parse_expression(expression["expression"], caller_context)
        else:
            member_name = expression["attributes"]["member_name"]
            member_type = expression["attributes"]["type"]
            # member_type = parse_type(UnknownType(expression["attributes"]["type"]), caller_context)
            children = expression["children"]
            assert len(children) == 1
            member_expression = parse_expression(children[0], caller_context)
        if str(member_expression) == "super":
            super_name = parse_super_name(expression, is_compact_ast)
            var, was_created = find_variable(super_name, caller_context, is_super=True)
            if var is None:
                raise VariableNotFound(f"Variable not found: {super_name}")
            if was_created:
                var.set_offset(src, caller_context.compilation_unit)
            sup = SuperIdentifier(var)
            sup.set_offset(src, caller_context.compilation_unit)
            return sup
        member_access = MemberAccess(member_name, member_type, member_expression)
        member_access.set_offset(src, caller_context.compilation_unit)
        if str(member_access) in SOLIDITY_VARIABLES_COMPOSED:
            id_idx = Identifier(SolidityVariableComposed(str(member_access)))
            id_idx.set_offset(src, caller_context.compilation_unit)
            return id_idx
        return member_access

    if name == "ElementaryTypeNameExpression":
        return _parse_elementary_type_name_expression(expression, is_compact_ast, caller_context)

    # NewExpression is not a root expression, it's always the child of another expression
    if name == "NewExpression":

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
                    if "name" not in type_name:
                        name_type = type_name["pathNode"]["name"]
                    else:
                        name_type = type_name["name"]

                    array_type = parse_type(UnknownType(name_type), caller_context)
                else:
                    array_type = parse_type(
                        UnknownType(type_name["attributes"]["name"]), caller_context
                    )
            elif type_name[caller_context.get_key()] == "FunctionTypeName":
                array_type = parse_type(type_name, caller_context)
            else:
                raise ParsingError(f"Incorrect type array {type_name}")
            array = NewArray(depth, array_type)
            array.set_offset(src, caller_context.compilation_unit)
            return array

        if type_name[caller_context.get_key()] == "ElementaryTypeName":
            if is_compact_ast:
                elem_type = ElementaryType(type_name["name"])
            else:
                elem_type = ElementaryType(type_name["attributes"]["name"])
            new_elem = NewElementaryType(elem_type)
            new_elem.set_offset(src, caller_context.compilation_unit)
            return new_elem

        assert type_name[caller_context.get_key()] == "UserDefinedTypeName"

        if is_compact_ast:

            # Changed introduced in Solidity 0.8
            # see https://github.com/crytic/slither/issues/794

            # TODO explore more the changes introduced in 0.8 and the usage of pathNode/IdentifierPath
            if "name" not in type_name:
                assert "pathNode" in type_name and "name" in type_name["pathNode"]
                contract_name = type_name["pathNode"]["name"]
            else:
                contract_name = type_name["name"]
        else:
            contract_name = type_name["attributes"]["name"]
        new = NewContract(contract_name)
        new.set_offset(src, caller_context.compilation_unit)
        return new

    if name == "ModifierInvocation":

        if is_compact_ast:
            called = parse_expression(expression["modifierName"], caller_context)
            arguments = []
            if expression.get("arguments", None):
                arguments = [parse_expression(a, caller_context) for a in expression["arguments"]]
        else:
            children = expression["children"]
            called = parse_expression(children[0], caller_context)
            arguments = [parse_expression(a, caller_context) for a in children[1::]]

        call = CallExpression(called, arguments, "Modifier")
        call.set_offset(src, caller_context.compilation_unit)
        return call

    if name == "IndexRangeAccess":
        # For now, we convert array slices to a direct array access
        # As a result the generated IR will lose the slices information
        # As far as I understand, array slice are only used in abi.decode
        # https://solidity.readthedocs.io/en/v0.6.12/types.html
        # TODO: Investigate array slices usage and implication for the IR
        base = parse_expression(expression["baseExpression"], caller_context)
        return base

    # Introduced with solc 0.8
    if name == "IdentifierPath":

        if caller_context.is_compact_ast:
            value = expression["name"]

            if "referencedDeclaration" in expression:
                referenced_declaration = expression["referencedDeclaration"]
            else:
                referenced_declaration = None

            var, was_created = find_variable(value, caller_context, referenced_declaration)
            if was_created:
                var.set_offset(src, caller_context.compilation_unit)

            identifier = Identifier(var)
            identifier.set_offset(src, caller_context.compilation_unit)
            return identifier

        raise ParsingError("IdentifierPath not currently supported for the legacy ast")

    raise ParsingError(f"Expression not parsed {name}")
