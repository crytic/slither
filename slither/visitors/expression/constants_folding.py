from fractions import Fraction
from typing import Union
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
)
from slither.core.variables import Variable
from slither.utils.integer_conversion import convert_string_to_fraction, convert_string_to_int
from slither.visitors.expression.expression import ExpressionVisitor
from slither.core.solidity_types.elementary_type import ElementaryType


class NotConstant(Exception):
    pass


KEY = "ConstantFolding"

CONSTANT_TYPES_OPERATIONS = Union[
    Literal, BinaryOperation, UnaryOperation, Identifier, TupleExpression, TypeConversion
]


def get_val(expression: CONSTANT_TYPES_OPERATIONS) -> Union[bool, int, Fraction, str]:
    val = expression.context[KEY]
    # we delete the item to reduce memory use
    del expression.context[KEY]
    return val


def set_val(expression: CONSTANT_TYPES_OPERATIONS, val: Union[bool, int, Fraction, str]) -> None:
    expression.context[KEY] = val


class ConstantFolding(ExpressionVisitor):
    def __init__(
        self, expression: CONSTANT_TYPES_OPERATIONS, custom_type: Union[str, "ElementaryType"]
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

    # pylint: disable=import-outside-toplevel
    def _post_identifier(self, expression: Identifier) -> None:
        from slither.core.declarations.solidity_variables import SolidityFunction

        if isinstance(expression.value, Variable):
            if expression.value.is_constant:
                expr = expression.value.expression
                # assumption that we won't have infinite loop
                # Everything outside of literal
                if isinstance(
                    expr,
                    (BinaryOperation, UnaryOperation, Identifier, TupleExpression, TypeConversion),
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
            raise NotConstant

    # pylint: disable=too-many-branches,too-many-statements
    def _post_binary_operation(self, expression: BinaryOperation) -> None:
        expression_left = expression.expression_left
        expression_right = expression.expression_right
        if not isinstance(
            expression_left,
            (Literal, BinaryOperation, UnaryOperation, Identifier, TupleExpression, TypeConversion),
        ):
            raise NotConstant
        if not isinstance(
            expression_right,
            (Literal, BinaryOperation, UnaryOperation, Identifier, TupleExpression, TypeConversion),
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
        called = get_val(expression.called)
        args = [get_val(arg) for arg in expression.arguments]
        if called.name == "keccak256(bytes)":
            digest = keccak.new(digest_bits=256)
            digest.update(str(args[0]).encode("utf-8"))
            set_val(expression, digest.digest())
        else:
            raise NotConstant

    def _post_conditional_expression(self, expression: expressions.ConditionalExpression) -> None:
        raise NotConstant

    def _post_elementary_type_name_expression(
        self, expression: expressions.ElementaryTypeNameExpression
    ) -> None:
        raise NotConstant

    def _post_index_access(self, expression: expressions.IndexAccess) -> None:
        raise NotConstant

    def _post_member_access(self, expression: expressions.MemberAccess) -> None:
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
        else:
            value = convert_string_to_fraction(expr.converted_value)
        set_val(expression, value)
