from typing import TYPE_CHECKING, Optional

from slither.core.source_mapping.source_mapping import SourceMapping

if TYPE_CHECKING:
    from slither.core.declarations import Contract


class ChildContract(SourceMapping):
    def __init__(self) -> None:
        super().__init__()
        # TODO remove all the setters for the child objects
        # And make it a constructor arguement
        # This will remove the optional
        self._contract: Optional["Contract"] = None

    def set_contract(self, contract: "Contract") -> None:
        self._contract = contract

    @property
    def contract(self) -> "Contract":
        return self._contract  # type: ignore
