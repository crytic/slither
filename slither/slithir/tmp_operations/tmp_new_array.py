from slither.core.solidity_types.type import Type
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.variables.temporary import TemporaryVariable


class TmpNewArray(OperationWithLValue):
    def __init__(
        self,
        array_type: Type,
        lvalue: TemporaryVariable,
    ) -> None:
        super().__init__()
        assert isinstance(array_type, Type)
        self._array_type = array_type
        self._lvalue = lvalue

    @property
    def array_type(self) -> Type:
        return self._array_type

    @property
    def read(self):
        return []

    def __str__(self):
        return f"{self.lvalue} = new {self.array_type}"
