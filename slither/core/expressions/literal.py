from slither.core.expressions.expression import Expression
from slither.utils.arithmetic import convert_subdenomination

class Literal(Expression):

    def __init__(self, value, type, subdenomination=None):
        super(Literal, self).__init__()
        self._value = value
        self._type = type
        self._subdenomination = subdenomination

    @property
    def value(self):
        return self._value

    @property
    def type(self):
        return self._type

    @property
    def subdenomination(self):
        return self._subdenomination

    def __str__(self):
        if self.subdenomination:
            return str(convert_subdenomination(self._value, self.subdenomination))
        # be sure to handle any character
        return str(self._value)
