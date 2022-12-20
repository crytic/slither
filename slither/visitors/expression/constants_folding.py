from fractions import Fraction
from slither.core.expressions import (
    BinaryOperationType,
    Literal,
    UnaryOperationType,
    Identifier,
    BinaryOperation,
    UnaryOperation,
)
from slither.utils.integer_conversion import convert_string_to_fraction, convert_string_to_int
from slither.visitors.expression.expression import ExpressionVisitor


class NotConstant(Exception):
    pass


KEY = "ConstantFolding"


def get_val(expression):
    val = expression.context[KEY]
    # we delete the item to reduce memory use
    del expression.context[KEY]
    return val


def set_val(expression, val):
    expression.context[KEY] = val


class ConstantFolding(ExpressionVisitor):
    def __init__(self, expression, custom_type):
        self._type = custom_type
        super().__init__(expression)

    def result(self):
        value = get_val(self._expression)
        if isinstance(value, Fraction):
            value = int(value)
            # emulate 256-bit wrapping
            if str(self._type).startswith("uint"):
                value = value & (2**256 - 1)
        return Literal(value, self._type)

    def _post_identifier(self, expression: Identifier):
        if not expression.value.is_constant:
            raise NotConstant
        expr = expression.value.expression
        # assumption that we won't have infinite loop
        if not isinstance(expr, Literal):
            cf = ConstantFolding(expr, self._type)
            expr = cf.result()
        set_val(expression, convert_string_to_int(expr.converted_value))

    # pylint: disable=too-many-branches
    def _post_binary_operation(self, expression: BinaryOperation):
        left = get_val(expression.expression_left)
        right = get_val(expression.expression_right)
        if expression.type == BinaryOperationType.POWER:
            set_val(expression, left**right)
        elif expression.type == BinaryOperationType.MULTIPLICATION:
            set_val(expression, left * right)
        elif expression.type == BinaryOperationType.DIVISION:
            set_val(expression, left / right)
        elif expression.type == BinaryOperationType.MODULO:
            set_val(expression, left % right)
        elif expression.type == BinaryOperationType.ADDITION:
            set_val(expression, left + right)
        elif expression.type == BinaryOperationType.SUBTRACTION:
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

    def _post_unary_operation(self, expression: UnaryOperation):
        # Case of uint a = -7; uint[-a] arr;
        if expression.type == UnaryOperationType.MINUS_PRE:
            expr = expression.expression
            if not isinstance(expr, Literal):
                cf = ConstantFolding(expr, self._type)
                expr = cf.result()
            assert isinstance(expr, Literal)
            set_val(expression, -convert_string_to_fraction(expr.converted_value))
        else:
            raise NotConstant

    def _post_literal(self, expression: Literal):
        if expression.converted_value in ["true", "false"]:
            set_val(expression, expression.converted_value)
        else:
            try:
                set_val(expression, convert_string_to_fraction(expression.converted_value))
            except ValueError as e:
                raise NotConstant from e

    def _post_assignement_operation(self, expression):
        raise NotConstant

    def _post_call_expression(self, expression):
        raise NotConstant

    def _post_conditional_expression(self, expression):
        raise NotConstant

    def _post_elementary_type_name_expression(self, expression):
        raise NotConstant

    def _post_index_access(self, expression):
        raise NotConstant

    def _post_member_access(self, expression):
        raise NotConstant

    def _post_new_array(self, expression):
        raise NotConstant

    def _post_new_contract(self, expression):
        raise NotConstant

    def _post_new_elementary_type(self, expression):
        raise NotConstant

    def _post_tuple_expression(self, expression):
        if expression.expressions:
            if len(expression.expressions) == 1:
                cf = ConstantFolding(expression.expressions[0], self._type)
                expr = cf.result()
                assert isinstance(expr, Literal)
                set_val(expression, convert_string_to_fraction(expr.converted_value))
                return
        raise NotConstant

    def _post_type_conversion(self, expression):
        cf = ConstantFolding(expression.expression, self._type)
        expr = cf.result()
        assert isinstance(expr, Literal)
        set_val(expression, convert_string_to_fraction(expr.converted_value))
