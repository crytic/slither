from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slither.core.declarations import Contract


class ChildContract:
    def __init__(self):
        super(ChildContract, self).__init__()
        self._contract = None

    def set_contract(self, contract: "Contract"):
        self._contract = contract

    @property
    def contract(self) -> "Contract":
        return self._contract
