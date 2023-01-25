from .operation import Operation
from typing import Any, List


class Nop(Operation):
    @property
    def read(self) -> List[Any]:
        return []

    @property
    def used(self):
        return []

    def __str__(self):
        return "NOP"
