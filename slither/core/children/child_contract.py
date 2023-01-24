from typing import TYPE_CHECKING

from slither.core.source_mapping.source_mapping import SourceMapping

if TYPE_CHECKING:
    from slither.core.declarations import Contract


class ChildContract(SourceMapping):
    def __init__(self) -> None:
        super().__init__()
        self._contract = None

    def set_contract(self, contract: "Contract") -> None:
        self._contract = contract

    @property
    def contract(self) -> "Contract":
        return self._contract
