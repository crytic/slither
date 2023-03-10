from slither.visitors.expression.expression import ExpressionVisitor
from slither.core.expressions.conditional_expression import ConditionalExpression


class HasConditional(ExpressionVisitor):
    def result(self) -> bool:
        # == True, to convert None to false
        return self._result is True

    def _post_conditional_expression(self, expression: ConditionalExpression) -> None:
        #        if self._result is True:
        #            raise('Slither does not support nested ternary operator')
        self._result = True
