from slither.core.expressions.expression import Expression

class Literal(Expression):

    def __init__(self, value, type):
        super(Literal, self).__init__()
        self._value = value
        self._type = type

    @property
    def value(self):
        return self._value

    @property
    def type(self):
        return self._type

    def __str__(self):
        # be sure to handle any character
        return str(self._value)
