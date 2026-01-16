from fractions import Fraction
from Crypto.Hash import keccak

from slither.core import expressions
from slither.core.expressions import (
    BinaryOperationType,
    Literal,
    UnaryOperationType,
    Identifier,
    BinaryOperation,
    UnaryOperation,
    TupleExpression,
    TypeConversion,
    CallExpression,
    MemberAccess,
)
from slither.core.expressions.elementary_type_name_expression import ElementaryTypeNameExpression
from slither.core.variables import Variable
from slither.utils.integer_conversion import convert_string_to_fraction, convert_string_to_int
from slither.visitors.expression.expression import ExpressionVisitor
from slither.core.solidity_types.elementary_type import ElementaryType


class NotConstant(Exception):
    pass


KEY = "ConstantFolding"

CONSTANT_TYPES_OPERATIONS = (
    Literal
    | BinaryOperation
    | UnaryOperation
    | Identifier
    | TupleExpression
    | TypeConversion
    | MemberAccess
)


def get_val(expression: CONSTANT_TYPES_OPERATIONS) -> bool | int | Fraction | str:
    val = expression.context[KEY]
    # we delete the item to reduce memory use
    del expression.context[KEY]
    return val


def set_val(expression: CONSTANT_TYPES_OPERATIONS, val: bool | int | Fraction | str) -> None:
    expression.context[KEY] = val


class ConstantFolding(ExpressionVisitor):
    def __init__(
        self, expression: CONSTANT_TYPES_OPERATIONS, custom_type: str | ElementaryType
    ) -> None:
        if isinstance(custom_type, str):
            custom_type = ElementaryType(custom_type)
        self._type: ElementaryType = custom_type
        super().__init__(expression)

    @property
    def expression(self) -> CONSTANT_TYPES_OPERATIONS:
        # We make the assumption that the expression is always a CONSTANT_TYPES_OPERATIONS
        # Other expression are not supported for constant unfolding
        return self._expression  # type: ignore

    def result(self) -> "Literal":
        value = get_val(self.expression)
        if isinstance(value, Fraction):
            value = int(value)
            # emulate 256-bit wrapping
            if str(self._type).startswith("uint"):
                value = value & (2**256 - 1)
        return Literal(value, self._type)

    def _post_identifier(self, expression: Identifier) -> None:
        from slither.core.declarations.solidity_variables import SolidityFunction
        from slither.core.declarations.enum import Enum
        from slither.core.solidity_types.type_alias import TypeAlias
        from slither.core.declarations.contract import Contract

        if isinstance(expression.value, Variable):
            if expression.value.is_constant:
                expr = expression.value.expression
                # assumption that we won't have infinite loop
                # Everything outside of literal
                if isinstance(
                    expr,
                    (
                        BinaryOperation,
                        UnaryOperation,
                        Identifier,
                        TupleExpression,
                        TypeConversion,
                        MemberAccess,
                    ),
                ):
                    cf = ConstantFolding(expr, self._type)
                    expr = cf.result()
                assert isinstance(expr, Literal)
                set_val(expression, convert_string_to_int(expr.converted_value))
            else:
                raise NotConstant
        elif isinstance(expression.value, SolidityFunction):
            set_val(expression, expression.value)
        else:
            # Enum: We don't want to raise an error for a direct access to an Enum as they can be converted to a constant value
            # We can't handle it here because we don't have the field accessed so we do it in _post_member_access
            # TypeAlias: Support when a .wrap() is done with a constant
            # Contract: Support when a constatn is use from a different contract
            if not isinstance(expression.value, (Enum, TypeAlias, Contract)):
                raise NotConstant

    def _post_binary_operation(self, expression: BinaryOperation) -> None:
        expression_left = expression.expression_left
        expression_right = expression.expression_right
        if not isinstance(
            expression_left,
            (
                Literal,
                BinaryOperation,
                UnaryOperation,
                Identifier,
                TupleExpression,
                TypeConversion,
                MemberAccess,
            ),
        ):
            raise NotConstant
        if not isinstance(
            expression_right,
            (
                Literal,
                BinaryOperation,
                UnaryOperation,
                Identifier,
                TupleExpression,
                TypeConversion,
                MemberAccess,
            ),
        ):
            raise NotConstant
        left = get_val(expression_left)
        right = get_val(expression_right)

        if (
            expression.type == BinaryOperationType.POWER
            and isinstance(left, (int, Fraction))
            and isinstance(right, (int, Fraction))
        ):
            set_val(expression, left**right)  # type: ignore
        elif (
            expression.type == BinaryOperationType.MULTIPLICATION
            and isinstance(left, (int, Fraction))
            and isinstance(right, (int, Fraction))
        ):
            set_val(expression, left * right)
        elif (
            expression.type == BinaryOperationType.DIVISION
            and isinstance(left, (int, Fraction))
            and isinstance(right, (int, Fraction))
        ):
            # TODO: maybe check for right + left to be int to use // ?
            set_val(expression, left // right if isinstance(right, int) else left / right)
        elif (
            expression.type == BinaryOperationType.MODULO
            and isinstance(left, (int, Fraction))
            and isinstance(right, (int, Fraction))
        ):
            set_val(expression, left % right)
        elif (
            expression.type == BinaryOperationType.ADDITION
            and isinstance(left, (int, Fraction))
            and isinstance(right, (int, Fraction))
        ):
            set_val(expression, left + right)
        elif (
            expression.type == BinaryOperationType.SUBTRACTION
            and isinstance(left, (int, Fraction))
            and isinstance(right, (int, Fraction))
        ):
            set_val(expression, left - right)
        # Convert to int for operations not supported by Fraction
        elif expression.type == BinaryOperationType.LEFT_SHIFT:
            set_val(expression, int(left) << int(right))
        elif expression.type == BinaryOperationType.RIGHT_SHIFT:
            set_val(expression, int(left) >> int(right))
        elif expression.type == BinaryOperationType.AND:
            set_val(expression, int(left) & int(right))
        elif expression.type == BinaryOperationType.CARET:
            set_val(expression, int(left) ^ int(right))
        elif expression.type == BinaryOperationType.OR:
            set_val(expression, int(left) | int(right))
        elif expression.type == BinaryOperationType.LESS:
            set_val(expression, int(left) < int(right))
        elif expression.type == BinaryOperationType.LESS_EQUAL:
            set_val(expression, int(left) <= int(right))
        elif expression.type == BinaryOperationType.GREATER:
            set_val(expression, int(left) > int(right))
        elif expression.type == BinaryOperationType.GREATER_EQUAL:
            set_val(expression, int(left) >= int(right))
        elif expression.type == BinaryOperationType.EQUAL:
            set_val(expression, int(left) == int(right))
        elif expression.type == BinaryOperationType.NOT_EQUAL:
            set_val(expression, int(left) != int(right))
        # Convert boolean literals from string to bool
        elif expression.type == BinaryOperationType.ANDAND:
            set_val(expression, left == "true" and right == "true")
        elif expression.type == BinaryOperationType.OROR:
            set_val(expression, left == "true" or right == "true")
        else:
            raise NotConstant

    def _post_unary_operation(self, expression: UnaryOperation) -> None:
        # Case of uint a = -7; uint[-a] arr;
        if expression.type == UnaryOperationType.MINUS_PRE:
            expr = expression.expression
            # Everything outside of literal
            if isinstance(
                expr, (BinaryOperation, UnaryOperation, Identifier, TupleExpression, TypeConversion)
            ):
                cf = ConstantFolding(expr, self._type)
                expr = cf.result()
            assert isinstance(expr, Literal)
            set_val(expression, -convert_string_to_fraction(expr.converted_value))
        else:
            raise NotConstant

    def _post_literal(self, expression: Literal) -> None:
        if str(expression.type) == "bool":
            set_val(expression, expression.converted_value)
        elif str(expression.type) == "string":
            set_val(expression, expression.converted_value)
        else:
            try:
                set_val(expression, convert_string_to_fraction(expression.converted_value))
            except ValueError as e:
                raise NotConstant from e

    def _post_assignement_operation(self, expression: expressions.AssignmentOperation) -> None:
        raise NotConstant

    def _post_call_expression(self, expression: expressions.CallExpression) -> None:
        from slither.core.declarations.solidity_variables import SolidityFunction
        from slither.core.declarations.enum import Enum
        from slither.core.solidity_types import TypeAlias

        if (
            isinstance(expression.called, Identifier)
            and expression.called.value == SolidityFunction("type()")
            and len(expression.arguments) == 1
            and (
                isinstance(expression.arguments[0], ElementaryTypeNameExpression)
                or (
                    isinstance(expression.arguments[0], Identifier)
                    and isinstance(expression.arguments[0].value, Enum)
                )
            )
        ):
            # Returning early to support type(ElemType).max/min or type(MyEnum).max/min
            return
        if (
            isinstance(expression.called.expression, Identifier)
            and isinstance(expression.called.expression.value, TypeAlias)
            and isinstance(expression.called, MemberAccess)
            and expression.called.member_name == "wrap"
            and len(expression.arguments) == 1
        ):
            # Handle constants in .wrap of user defined type
            set_val(expression, get_val(expression.arguments[0]))
            return

        called = get_val(expression.called)
        args = [get_val(arg) for arg in expression.arguments]
        if called.name == "keccak256(bytes)":
            digest = keccak.new(digest_bits=256)
            digest.update(str(args[0]).encode("utf8"))
            set_val(expression, digest.digest())
        else:
            raise NotConstant

    def _post_conditional_expression(self, expression: expressions.ConditionalExpression) -> None:
        raise NotConstant

    def _post_elementary_type_name_expression(
        self, expression: expressions.ElementaryTypeNameExpression
    ) -> None:
        # We don't have to raise an exception to support type(uint112).max or similar
        pass

    def _post_index_access(self, expression: expressions.IndexAccess) -> None:
        raise NotConstant

    def _post_member_access(self, expression: expressions.MemberAccess) -> None:
        from slither.core.declarations import (
            SolidityFunction,
            Contract,
            EnumContract,
            EnumTopLevel,
            Enum,
        )
        from slither.core.solidity_types import UserDefinedType, TypeAlias

        if isinstance(expression.expression, CallExpression) and expression.member_name in [
            "min",
            "max",
        ]:
            if isinstance(expression.expression.called, Identifier):
                if expression.expression.called.value == SolidityFunction("type()"):
                    assert len(expression.expression.arguments) == 1
                    type_expression_found = expression.expression.arguments[0]
                    type_found: ElementaryType | UserDefinedType
                    if isinstance(type_expression_found, ElementaryTypeNameExpression):
                        type_expression_found_type = type_expression_found.type
                        assert isinstance(type_expression_found_type, ElementaryType)
                        type_found = type_expression_found_type
                        value = (
                            type_found.max if expression.member_name == "max" else type_found.min
                        )
                        set_val(expression, value)
                        return
                    # type(enum).max/min
                    # Case when enum is in another contract e.g. type(C.E).max
                    if isinstance(type_expression_found, MemberAccess):
                        contract = type_expression_found.expression.value
                        assert isinstance(contract, Contract)
                        for enum in contract.enums:
                            if enum.name == type_expression_found.member_name:
                                type_found_in_expression = enum
                                type_found = UserDefinedType(enum)
                                break
                    else:
                        assert isinstance(type_expression_found, Identifier)
                        type_found_in_expression = type_expression_found.value
                        assert isinstance(type_found_in_expression, (EnumContract, EnumTopLevel))
                        type_found = UserDefinedType(type_found_in_expression)
                    value = (
                        type_found_in_expression.max
                        if expression.member_name == "max"
                        else type_found_in_expression.min
                    )
                    set_val(expression, value)
                    return
        elif isinstance(expression.expression, Identifier) and isinstance(
            expression.expression.value, Enum
        ):
            # Handle direct access to enum field
            set_val(expression, expression.expression.value.values.index(expression.member_name))
            return
        elif isinstance(expression.expression, Identifier) and isinstance(
            expression.expression.value, TypeAlias
        ):
            # User defined type .wrap call handled in _post_call_expression
            return
        elif (
            isinstance(expression.expression, TypeConversion)
            and expression.expression.type == ElementaryType("address")
            and expression.member_name in ["balance", "code", "codehash"]
        ):
            # We need to raise NotConstant for these case here otherwise expression.expression.value would crash in the following condition
            # because TypeConversion does not have a value. See https://github.com/crytic/slither/issues/2717
            raise NotConstant
        elif (
            isinstance(expression.expression.value, Contract)
            and expression.member_name in expression.expression.value.variables_as_dict
            and expression.expression.value.variables_as_dict[expression.member_name].is_constant
        ):
            # Handles when a constant is accessed on another contract
            variables = expression.expression.value.variables_as_dict
            if isinstance(variables[expression.member_name].expression, MemberAccess):
                self._post_member_access(variables[expression.member_name].expression)
                set_val(expression, get_val(variables[expression.member_name].expression))
                return

            # If the variable is a Literal we convert its value to int
            if isinstance(variables[expression.member_name].expression, Literal):
                value = convert_string_to_int(
                    variables[expression.member_name].expression.converted_value
                )
            # If the variable is a UnaryOperation we need convert its value to int
            # and replacing possible spaces
            elif isinstance(variables[expression.member_name].expression, UnaryOperation):
                value = convert_string_to_int(
                    str(variables[expression.member_name].expression).replace(" ", "")
                )
            else:
                value = variables[expression.member_name].expression

            set_val(expression, value)
            return

        raise NotConstant

    def _post_new_array(self, expression: expressions.NewArray) -> None:
        raise NotConstant

    def _post_new_contract(self, expression: expressions.NewContract) -> None:
        raise NotConstant

    def _post_new_elementary_type(self, expression: expressions.NewElementaryType) -> None:
        raise NotConstant

    def _post_tuple_expression(self, expression: expressions.TupleExpression) -> None:
        if expression.expressions:
            if len(expression.expressions) == 1:
                first_expr = expression.expressions[0]
                if not isinstance(
                    first_expr,
                    (
                        Literal,
                        BinaryOperation,
                        UnaryOperation,
                        Identifier,
                        TupleExpression,
                        TypeConversion,
                    ),
                ):
                    raise NotConstant
                cf = ConstantFolding(first_expr, self._type)
                expr = cf.result()
                assert isinstance(expr, Literal)
                set_val(expression, convert_string_to_fraction(expr.converted_value))
                return
        raise NotConstant

    def _post_type_conversion(self, expression: expressions.TypeConversion) -> None:
        expr = expression.expression
        if not isinstance(
            expr,
            (
                Literal,
                BinaryOperation,
                UnaryOperation,
                Identifier,
                TupleExpression,
                TypeConversion,
                CallExpression,
                MemberAccess,
            ),
        ):
            raise NotConstant
        cf = ConstantFolding(expr, self._type)
        expr = cf.result()
        assert isinstance(expr, Literal)
        if str(expression.type).startswith("uint") and isinstance(expr.value, bytes):
            value = int.from_bytes(expr.value, "big")
        elif str(expression.type).startswith("byte") and isinstance(expr.value, int):
            value = int.to_bytes(expr.value, 32, "big")
        elif str(expression.type).startswith("byte") and isinstance(expr.value, str):
            value = expr.value
        else:
            value = convert_string_to_fraction(expr.converted_value)
        set_val(expression, value)
