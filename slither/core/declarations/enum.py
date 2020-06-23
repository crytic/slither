from typing import List, TYPE_CHECKING

from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.children.child_contract import ChildContract

if TYPE_CHECKING:
    from slither.core.declarations import Contract


class Enum(ChildContract, SourceMapping):
    def __init__(self, name: str, canonical_name: str, values: List[str]):
        super().__init__()
        self._name = name
        self._canonical_name = canonical_name
        self._values = values

    @property
    def canonical_name(self) -> str:
        return self._canonical_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def values(self) -> List[str]:
        return self._values

    def is_declared_by(self, contract: "Contract") -> bool:
        """
        Check if the element is declared by the contract
        :param contract:
        :return:
        """
        return self.contract == contract

    def __str__(self):
        return self.name
