from slither.visitors.expression.expression import ExpressionVisitor
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.index_access import IndexAccess

from slither.visitors.expression.right_value import RightValue

key = "FindPush"


def get(expression):
    val = expression.context[key]
    # we delete the item to reduce memory use
    del expression.context[key]
    return val


def set_val(expression, val):
    expression.context[key] = val


class FindPush(ExpressionVisitor):
    def result(self):
        if self._result is None:
            self._result = list(set(get(self.expression)))
        return self._result

    def _post_assignement_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = left + right
        set_val(expression, val)

    def _post_binary_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = left + right
        set_val(expression, val)

    def _post_call_expression(self, expression):
        called = get(expression.called)
        args = [get(a) for a in expression.arguments if a]
        args = [item for sublist in args for item in sublist]
        val = called + args
        set_val(expression, val)

    def _post_conditional_expression(self, expression):
        if_expr = get(expression.if_expression)
        else_expr = get(expression.else_expression)
        then_expr = get(expression.then_expression)
        val = if_expr + else_expr + then_expr
        set_val(expression, val)

    def _post_elementary_type_name_expression(self, expression):
        set_val(expression, [])

    # save only identifier expression
    def _post_identifier(self, expression):
        set_val(expression, [])

    def _post_index_access(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = left + right
        set_val(expression, val)

    def _post_literal(self, expression):
        set_val(expression, [])

    def _post_member_access(self, expression):
        val = []
        if expression.member_name == "push":
            right = RightValue(expression.expression)
            val = right.result()
        set_val(expression, val)

    def _post_new_array(self, expression):
        set_val(expression, [])

    def _post_new_contract(self, expression):
        set_val(expression, [])

    def _post_new_elementary_type(self, expression):
        set_val(expression, [])

    def _post_tuple_expression(self, expression):
        expressions = [get(e) for e in expression.expressions if e]
        val = [item for sublist in expressions for item in sublist]
        set_val(expression, val)

    def _post_type_conversion(self, expression):
        expr = get(expression.expression)
        val = expr
        set_val(expression, val)

    def _post_unary_operation(self, expression):
        expr = get(expression.expression)
        val = expr
        set_val(expression, val)
