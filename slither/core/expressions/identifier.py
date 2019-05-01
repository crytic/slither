from slither.core.expressions.expression_typed import ExpressionTyped

class Identifier(ExpressionTyped):

    def __init__(self, value):
        super(Identifier, self).__init__()
        self._value = value

    @property
    def value(self):
        return self._value

    def __str__(self):
        return str(self._value)

