from typing import List

from .expression import Expression


class ConditionalExpression(Expression):
    def __init__(self, if_expression, then_expression, else_expression):
        assert isinstance(if_expression, Expression)
        assert isinstance(then_expression, Expression)
        assert isinstance(else_expression, Expression)
        super(ConditionalExpression, self).__init__()
        self._if_expression: Expression = if_expression
        self._then_expression: Expression = then_expression
        self._else_expression: Expression = else_expression

    @property
    def expressions(self) -> List[Expression]:
        return [self._if_expression, self._then_expression, self._else_expression]

    @property
    def if_expression(self) -> Expression:
        return self._if_expression

    @property
    def else_expression(self) -> Expression:
        return self._else_expression

    @property
    def then_expression(self) -> Expression:
        return self._then_expression

    def __str__(self):
        return (
            "if "
            + str(self._if_expression)
            + " then "
            + str(self._then_expression)
            + " else "
            + str(self._else_expression)
        )
