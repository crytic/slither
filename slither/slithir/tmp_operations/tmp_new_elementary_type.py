from typing import List

from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.solidity_types.elementary_type import ElementaryType


class TmpNewElementaryType(OperationWithLValue):
    def __init__(self, new_type: ElementaryType, lvalue):
        assert isinstance(new_type, ElementaryType)
        super().__init__()
        self._type: ElementaryType = new_type
        self._lvalue = lvalue

    @property
    def read(self) -> List:
        return []

    @property
    def type(self) -> ElementaryType:
        return self._type

    def __str__(self) -> str:
        return f"{self.lvalue} = new {self._type}"
