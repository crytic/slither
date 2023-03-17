from typing import Union, TYPE_CHECKING


from slither.core.expressions.expression import Expression
from slither.core.solidity_types.type import Type

if TYPE_CHECKING:
    from slither.core.solidity_types.elementary_type import ElementaryType
    from slither.core.solidity_types.type_alias import TypeAliasTopLevel


class NewArray(Expression):

    # note: dont conserve the size of the array if provided
    def __init__(
        self, depth: int, array_type: Union["TypeAliasTopLevel", "ElementaryType"]
    ) -> None:
        super().__init__()
        assert isinstance(array_type, Type)
        self._depth: int = depth
        self._array_type: Type = array_type

    @property
    def array_type(self) -> Type:
        return self._array_type

    @property
    def depth(self) -> int:
        return self._depth

    def __str__(self):
        return "new " + str(self._array_type) + "[]" * self._depth
