from typing import TYPE_CHECKING, Tuple

from slither.core.children.child_contract import ChildContract
from slither.core.declarations.top_level import TopLevel
from slither.core.solidity_types import Type

if TYPE_CHECKING:
    from slither.core.declarations import Contract
    from slither.core.scope.scope import FileScope


class TypeAlias(Type):
    def __init__(self, underlying_type: Type, name: str):
        super().__init__()
        self.name = name
        self.underlying_type = underlying_type

    @property
    def storage_size(self) -> Tuple[int, bool]:
        return self.underlying_type.storage_size

    def __hash__(self):
        return hash(str(self))


class TypeAliasTopLevel(TypeAlias, TopLevel):
    def __init__(self, underlying_type: Type, name: str, scope: "FileScope"):
        super().__init__(underlying_type, name)
        self.file_scope: "FileScope" = scope

    def __str__(self):
        return self.name


class TypeAliasContract(TypeAlias, ChildContract):
    def __init__(self, underlying_type: Type, name: str, contract: "Contract"):
        super().__init__(underlying_type, name)
        self._contract: "Contract" = contract

    def __str__(self):
        return self.contract.name + "." + self.name
