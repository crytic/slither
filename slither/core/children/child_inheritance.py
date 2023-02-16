from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from slither.core.declarations import Contract


class ChildInheritance:
    def __init__(self) -> None:
        super().__init__()
        # TODO remove all the setters for the child objects
        # And make it a constructor arguement
        # This will remove the optional
        self._contract_declarer: Optional["Contract"] = None

    def set_contract_declarer(self, contract: "Contract") -> None:
        self._contract_declarer = contract

    @property
    def contract_declarer(self) -> "Contract":
        return self._contract_declarer  # type: ignore
