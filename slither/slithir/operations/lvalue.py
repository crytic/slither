from typing import Any, List, Optional

from slither.core.variables import Variable
from slither.slithir.operations.operation import Operation


class OperationWithLValue(Operation):
    """
    Operation with a lvalue
    """

    def __init__(self) -> None:
        super().__init__()

        self._lvalue: Optional[Variable] = None

    @property
    def lvalue(self) -> Optional[Variable]:
        return self._lvalue

    @lvalue.setter
    def lvalue(self, lvalue: Variable) -> None:
        self._lvalue = lvalue

    @property
    def used(self) -> List[Optional[Any]]:
        return self.read + [self.lvalue]
