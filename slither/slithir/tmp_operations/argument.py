from enum import Enum
from typing import Optional, List

from slither.core.expressions.expression import Expression
from slither.slithir.operations.operation import Operation


class ArgumentType(Enum):
    CALL = 0
    VALUE = 1
    GAS = 2
    DATA = 3


class Argument(Operation):
    def __init__(self, argument: Expression) -> None:
        super().__init__()
        self._argument = argument
        self._type = ArgumentType.CALL
        self._callid: Optional[str] = None

    @property
    def argument(self) -> Expression:
        return self._argument

    @property
    def call_id(self) -> Optional[str]:
        return self._callid

    @call_id.setter
    def call_id(self, c: str) -> None:
        self._callid = c

    @property
    def read(self) -> List[Expression]:
        return [self.argument]

    def set_type(self, t: ArgumentType) -> None:
        assert isinstance(t, ArgumentType)
        self._type = t

    def get_type(self) -> ArgumentType:
        return self._type

    def __str__(self) -> str:
        call_id = "none"
        if self.call_id:
            call_id = f"(id ({self.call_id}))"
        return f"ARG_{self._type.name} {str(self._argument)} {call_id}"
