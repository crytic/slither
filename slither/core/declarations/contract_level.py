from typing import TYPE_CHECKING, Optional

from slither.core.source_mapping.source_mapping import SourceMapping

if TYPE_CHECKING:
    from slither.core.declarations import Contract


class ContractLevel(SourceMapping):
    """
    This class is used to represent objects that are at the contract level
    The opposite is TopLevel

    """

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
        assert self._contract
        return self._contract
