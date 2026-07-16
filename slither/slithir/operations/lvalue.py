from typing import Any

from slither.core.variables import Variable
from slither.slithir.operations.operation import Operation


class OperationWithLValue(Operation):
    """
    Operation with a lvalue
    """

    def __init__(self) -> None:
        super().__init__()

        self._lvalue: Variable | None = None

    @property
    def lvalue(self) -> Variable | None:
        return self._lvalue

    @lvalue.setter
    def lvalue(self, lvalue: Variable) -> None:
        self._lvalue = lvalue

    @property
    def used(self) -> list[Any | None]:
        return self.read + [self.lvalue]
