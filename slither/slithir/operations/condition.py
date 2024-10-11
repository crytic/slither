from typing import List

from slither.slithir.operations.operation import Operation
from slither.slithir.utils.utils import is_valid_rvalue, RVALUE


class Condition(Operation):
    """
    Condition
    Only present as last operation in conditional node
    """

    def __init__(
        self,
        value: RVALUE,
    ) -> None:
        assert is_valid_rvalue(value)
        super().__init__()
        self._value = value

    @property
    def read(
        self,
    ) -> List[RVALUE]:
        return [self.value]

    @property
    def value(self) -> RVALUE:
        return self._value

    def __str__(self) -> str:
        return f"CONDITION {self.value}"
