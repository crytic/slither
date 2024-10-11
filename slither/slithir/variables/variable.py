from slither.core.variables.variable import Variable


class SlithIRVariable(Variable):
    def __init__(self) -> None:
        super().__init__()
        self._index = 0

    @property
    def ssa_name(self) -> str:
        assert self.name
        return self.name

    def __str__(self) -> str:
        return self.ssa_name
