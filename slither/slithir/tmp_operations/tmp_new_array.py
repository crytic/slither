from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.solidity_types.type import Type
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.type_alias import TypeAliasTopLevel
from slither.slithir.variables.temporary import TemporaryVariable
from typing import Union


class TmpNewArray(OperationWithLValue):
    def __init__(self, depth: int, array_type: Union[TypeAliasTopLevel, ElementaryType], lvalue: TemporaryVariable) -> None:
        super().__init__()
        assert isinstance(array_type, Type)
        self._depth = depth
        self._array_type = array_type
        self._lvalue = lvalue

    @property
    def array_type(self) -> TypeAliasTopLevel:
        return self._array_type

    @property
    def read(self):
        return []

    @property
    def depth(self) -> int:
        return self._depth

    def __str__(self):
        return f"{self.lvalue} = new {self.array_type}{'[]' * self._depth}"
