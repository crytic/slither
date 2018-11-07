
from .expression import Expression

class ExpressionTyped(Expression):

    def __init__(self):
        super(ExpressionTyped, self).__init__()
        self._type = None

    @property
    def type(self):
        return self._type

