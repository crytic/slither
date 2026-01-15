from typing import Any, List, Optional, TypeVar

from slither.core.variables import Variable
from slither.slithir.operations.operation import Operation

VariableT = TypeVar("VariableT", bound=Variable)


class OperationWithLValue(Operation):
    """
    Operation with a lvalue
    """

    def __init__(self) -> None:
        super().__init__()

        self._lvalue: VariableT

    @property
    def lvalue(self) -> VariableT:
        return self._lvalue

    @lvalue.setter
    def lvalue(self, lvalue: VariableT) -> None:
        self._lvalue = lvalue

    @property
    def used(self) -> List[Optional[Any]]:
        return self.read + [self.lvalue]
