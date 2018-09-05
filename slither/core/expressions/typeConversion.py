from slither.core.expressions.expressionTyped import ExpressionTyped
from slither.core.expressions.expression import Expression
from slither.core.solidityTypes.type import Type


class TypeConversion(ExpressionTyped):

    def __init__(self, expression, expression_type):
        super(TypeConversion, self).__init__()
        assert isinstance(expression, Expression)
        assert isinstance(expression_type, Type)
        self._expression = expression
        self._type = expression_type

    @property
    def expression(self):
        return self._expression

    def __str__(self):
        return str(self.type) + '(' + str(self.expression) + ')'

