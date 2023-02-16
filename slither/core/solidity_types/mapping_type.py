from typing import Union, Tuple, TYPE_CHECKING, Any

from slither.core.solidity_types.type import Type

if TYPE_CHECKING:
    from slither.core.solidity_types.elementary_type import ElementaryType
    from slither.core.solidity_types.type_alias import TypeAliasTopLevel


class MappingType(Type):
    def __init__(
        self,
        type_from: "ElementaryType",
        type_to: Union["MappingType", "TypeAliasTopLevel", "ElementaryType"],
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
    def storage_size(self) -> Tuple[int, bool]:
        return 32, True

    @property
    def is_dynamic(self) -> bool:
        return True

    def __str__(self) -> str:
        return f"mapping({str(self._from)} => {str(self._to)})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MappingType):
            return False
        return self.type_from == other.type_from and self.type_to == other.type_to

    def __hash__(self) -> int:
        return hash(str(self))
