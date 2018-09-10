from slither.core.expressions.expression import Expression

class Literal(Expression):

    def __init__(self, value):
        super(Literal, self).__init__()
        self._value = value

    @property
    def value(self):
        return self._value

    def __str__(self):
        # be sure to handle any character
        return str(self._value)
