from typing import TYPE_CHECKING

from slither.core.expressions.expression import Expression

if TYPE_CHECKING:
    from slither.core.solidity_types.array_type import ArrayType


class NewArray(Expression):
    def __init__(self, array_type: "ArrayType") -> None:
        super().__init__()
        # pylint: disable=import-outside-toplevel
        from slither.core.solidity_types.array_type import ArrayType

        assert isinstance(array_type, ArrayType)
        self._array_type = array_type

    @property
    def array_type(self) -> "ArrayType":
        return self._array_type

    def __str__(self):
        return "new " + str(self._array_type)
