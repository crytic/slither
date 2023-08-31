from slither.core.expressions.identifier import Identifier


class SelfIdentifier(Identifier):
    def __str__(self):
        return "self." + str(self._value)
