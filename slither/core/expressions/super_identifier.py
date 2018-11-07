from slither.core.expressions.expression_typed import ExpressionTyped
from slither.core.expressions.identifier import Identifier

class SuperIdentifier(Identifier):

    def __str__(self):
        return 'super.' + str(self._value)

