from typing import Any, List
from slither.slithir.operations.operation import Operation


class OperationWithLValue(Operation):
    """
    Operation with a lvalue
    """

    def __init__(self) -> None:
        super().__init__()

        self._lvalue = None

    @property
    def lvalue(self):
        return self._lvalue

    @property
    def used(self) -> List[Any]:
        return self.read + [self.lvalue]

    @lvalue.setter
    def lvalue(self, lvalue):
        self._lvalue = lvalue
