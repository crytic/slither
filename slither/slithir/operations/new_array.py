from typing import List, Union, TYPE_CHECKING
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.operations.call import Call
from slither.core.solidity_types.type import Type

if TYPE_CHECKING:
    from slither.core.solidity_types.type_alias import TypeAliasTopLevel
    from slither.slithir.variables.constant import Constant
    from slither.slithir.variables.temporary import TemporaryVariable
    from slither.slithir.variables.temporary_ssa import TemporaryVariableSSA


class NewArray(Call, OperationWithLValue):
    def __init__(
        self,
        depth: int,
        array_type: "TypeAliasTopLevel",
        lvalue: Union["TemporaryVariableSSA", "TemporaryVariable"],
    ) -> None:
        super().__init__()
        assert isinstance(array_type, Type)
        self._depth = depth
        self._array_type = array_type

        self._lvalue = lvalue

    @property
    def array_type(self) -> "TypeAliasTopLevel":
        return self._array_type

    @property
    def read(self) -> List["Constant"]:
        return self._unroll(self.arguments)

    @property
    def depth(self) -> int:
        return self._depth

    def __str__(self):
        args = [str(a) for a in self.arguments]
        return f"{self.lvalue} = new {self.array_type}{'[]' * self.depth}({','.join(args)})"
