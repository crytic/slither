from slither.core.expressions.expression_typed import ExpressionTyped
from slither.core.expressions.expression import Expression
from slither.core.solidity_types.type import Type


class TypeConversion(ExpressionTyped):
    def __init__(self, expression, expression_type):
        super(TypeConversion, self).__init__()
        assert isinstance(expression, Expression)
        assert isinstance(expression_type, Type)
        self._expression: Expression = expression
        self._type: Type = expression_type

    @property
    def expression(self) -> Expression:
        return self._expression

    def __str__(self):
        return str(self.type) + "(" + str(self.expression) + ")"
