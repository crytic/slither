from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slither.core.declarations import Contract


class ChildInheritance:
    def __init__(self) -> None:
        super().__init__()
        self._contract_declarer = None

    def set_contract_declarer(self, contract: "Contract") -> None:
        self._contract_declarer = contract

    @property
    def contract_declarer(self) -> "Contract":
        return self._contract_declarer
