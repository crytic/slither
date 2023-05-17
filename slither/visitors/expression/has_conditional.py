from slither.core.expressions.expression import Expression
from slither.visitors.expression.expression import ExpressionVisitor
from slither.core.expressions.conditional_expression import ConditionalExpression


class HasConditional(ExpressionVisitor):
    def __init__(self, expression: Expression) -> None:
        self._result: bool = False
        super().__init__(expression)

    def result(self) -> bool:
        return self._result

    def _post_conditional_expression(self, expression: ConditionalExpression) -> None:
        self._result = True
