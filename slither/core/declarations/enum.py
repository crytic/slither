from typing import List

from slither.core.source_mapping.source_mapping import SourceMapping


class Enum(SourceMapping):
    def __init__(self, name: str, canonical_name: str, values: List[str]) -> None:
        super().__init__()
        self._name = name
        self._canonical_name = canonical_name
        self._values = values
        self._min = 0
        # The max value of an Enum is the index of the last element
        self._max = len(values) - 1

    @property
    def canonical_name(self) -> str:
        return self._canonical_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def values(self) -> List[str]:
        return self._values

    @property
    def min(self) -> int:
        return self._min

    @property
    def max(self) -> int:
        return self._max

    def __str__(self) -> str:
        return self.name
