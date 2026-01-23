from slither.core.variables.variable import Variable
from slither.slithir.operations import Operation


class Nop(Operation):
    @property
    def read(self) -> list[Variable]:
        return []

    @property
    def used(self):
        return []

    def __str__(self):
        return "NOP"
