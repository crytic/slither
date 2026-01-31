from typing import Union, TYPE_CHECKING, Any

from slither.core.solidity_types.type import Type

if TYPE_CHECKING:
    from slither.core.solidity_types.elementary_type import ElementaryType
    from slither.core.solidity_types.type_alias import TypeAlias


class MappingType(Type):
    def __init__(
        self,
        type_from: Union["ElementaryType", "TypeAlias"],
        type_to: Union["MappingType", "TypeAlias", "ElementaryType"],
    ) -> None:
        assert isinstance(type_from, Type)
        assert isinstance(type_to, Type)
        super().__init__()
        self._from = type_from
        self._to = type_to

    @property
    def type_from(self) -> Type:
        return self._from

    @property
    def type_to(self) -> Type:
        return self._to

    @property
    def storage_size(self) -> tuple[int, bool]:
        return 32, True

    @property
    def is_dynamic(self) -> bool:
        return True

    def __str__(self) -> str:
        return f"mapping({self._from!s} => {self._to!s})"

    def __eq__(self, other: Any) -> bool:
        # Use type() and direct attribute access for performance
        if type(other) is not MappingType:
            return False
        return self._from == other._from and self._to == other._to

    def __hash__(self) -> int:
        return hash(str(self))
