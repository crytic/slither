import logging

from .expression import ExpressionVisitor
from slither.core.expressions import BinaryOperationType, Literal

class NotConstant(Exception):
    pass


KEY = 'ConstantFolding'

def get_val(expression):
    val = expression.context[KEY]
    # we delete the item to reduce memory use
    del expression.context[KEY]
    return val

def set_val(expression, val):
    expression.context[KEY] = val

class ConstantFolding(ExpressionVisitor):

    def result(self):
        return Literal(int(get_val(self._expression)))

    def _post_identifier(self, expression):
        if not expression.value.is_constant:
            raise NotConstant
        expr = expression.value.expression
        # assumption that we won't have infinite loop
        if not isinstance(expr, Literal):
            cf = ConstantFolding(expr)
            expr = cf.result()
        set_val(expression, int(expr.value))

    def _post_binary_operation(self, expression):
        left = get_val(expression.expression_left)
        right = get_val(expression.expression_right)
        if expression.type  == BinaryOperationType.POWER:
            set_val(expression, left ** right)
        elif expression.type  == BinaryOperationType.MULTIPLICATION:
            set_val(expression, left * right)
        elif expression.type  == BinaryOperationType.DIVISION:
            set_val(expression, left / right)
        elif expression.type  == BinaryOperationType.MODULO:
            set_val(expression, left % right)
        elif expression.type  == BinaryOperationType.ADDITION:
            set_val(expression, left + right)
        elif expression.type  == BinaryOperationType.SUBTRACTION:
            if(left-right) <0:
                # Could trigger underflow
                raise NotConstant
            set_val(expression, left - right)
        elif expression.type  == BinaryOperationType.LEFT_SHIFT:
            set_val(expression, left << right)
        elif expression.type  == BinaryOperationType.RIGHT_SHIFT:
            set_val(expression, left >> right)
        else:
            raise NotConstant

    def _post_unary_operation(self, expression):
        raise NotConstant

    def _post_literal(self, expression):
        if expression.value.isdigit():
            set_val(expression, int(expression.value))
        else:
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
        raise NotConstant

    def _post_type_conversion(self, expression):
        raise NotConstant



