from slither.core.expressions import BinaryOperationType, Literal, UnaryOperationType
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
        return Literal(int(get_val(self._expression)), self._type)

    def _post_identifier(self, expression):
        if not expression.value.is_constant:
            raise NotConstant
        expr = expression.value.expression
        # assumption that we won't have infinite loop
        if not isinstance(expr, Literal):
            cf = ConstantFolding(expr, self._type)
            expr = cf.result()
        set_val(expression, convert_string_to_int(expr.value))

    def _post_binary_operation(self, expression):
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
            if (left - right) < 0:
                # Could trigger underflow
                raise NotConstant
            set_val(expression, left - right)
        elif expression.type == BinaryOperationType.LEFT_SHIFT:
            set_val(expression, left << right)
        elif expression.type == BinaryOperationType.RIGHT_SHIFT:
            set_val(expression, left >> right)
        else:
            raise NotConstant

    def _post_unary_operation(self, expression):
        # Case of uint a = -7; uint[-a] arr;
        if expression.type == UnaryOperationType.MINUS_PRE:
            expr = expression.expression
            if not isinstance(expr, Literal):
                cf = ConstantFolding(expr, self._type)
                expr = cf.result()
            assert isinstance(expr, Literal)
            set_val(expression, -convert_string_to_fraction(expr.value))
        else:
            raise NotConstant

    def _post_literal(self, expression):
        try:
            set_val(expression, convert_string_to_fraction(expression.value))
        except ValueError:
            raise NotConstant

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
                set_val(expression, convert_string_to_fraction(expr.value))
                return
        raise NotConstant

    def _post_type_conversion(self, expression):
        raise NotConstant
