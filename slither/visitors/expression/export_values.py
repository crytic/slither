from typing import Any, List
from slither.visitors.expression.expression import ExpressionVisitor
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.literal import Literal
from slither.core.expressions.binary_operation import BinaryOperation
from slither.core.expressions.expression import Expression
from slither.core.expressions.member_access import MemberAccess
from slither.core.expressions.tuple_expression import TupleExpression
from slither.core.expressions.type_conversion import TypeConversion


key = "ExportValues"


def get(expression: Expression) -> List[Any]:
    val = expression.context[key]
    # we delete the item to reduce memory use
    del expression.context[key]
    return val


def set_val(expression: Expression, val: List[Any]) -> None:
    expression.context[key] = val


class ExportValues(ExpressionVisitor):
    def result(self) -> List[Any]:
        if self._result is None:
            self._result = list(set(get(self.expression)))
        return self._result

    def _post_assignement_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = left + right
        set_val(expression, val)

    def _post_binary_operation(self, expression: BinaryOperation) -> None:
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = left + right
        set_val(expression, val)

    def _post_call_expression(self, expression: CallExpression) -> None:
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

    def _post_identifier(self, expression: Identifier) -> None:
        set_val(expression, [expression.value])

    def _post_index_access(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = left + right
        set_val(expression, val)

    def _post_literal(self, expression: Literal) -> None:
        set_val(expression, [])

    def _post_member_access(self, expression: MemberAccess) -> None:
        expr = get(expression.expression)
        val = expr
        set_val(expression, val)

    def _post_new_array(self, expression):
        set_val(expression, [])

    def _post_new_contract(self, expression):
        set_val(expression, [])

    def _post_new_elementary_type(self, expression):
        set_val(expression, [])

    def _post_tuple_expression(self, expression: TupleExpression) -> None:
        expressions = [get(e) for e in expression.expressions if e]
        val = [item for sublist in expressions for item in sublist]
        set_val(expression, val)

    def _post_type_conversion(self, expression: TypeConversion) -> None:
        expr = get(expression.expression)
        val = expr
        set_val(expression, val)

    def _post_unary_operation(self, expression):
        expr = get(expression.expression)
        val = expr
        set_val(expression, val)
