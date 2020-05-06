from enum import Enum
from typing import TYPE_CHECKING, Optional, List

from slither.slithir.operations.operation import Operation

if TYPE_CHECKING:
    from slither.core.variables.variable import Variable


class ArgumentType(Enum):
    CALL = 0
    VALUE = 1
    GAS = 2
    DATA = 3


class Argument(Operation):
    def __init__(self,
                 argument: "Variable"):
        super(Argument, self).__init__()
        self._argument: "Variable" = argument
        self._type = ArgumentType.CALL
        self._callid: Optional[str] = None  # only used if gas/value != 0

    @property
    def argument(self) -> "Variable":
        return self._argument

    @property
    def call_id(self) -> Optional[str]:
        return self._callid

    @call_id.setter
    def call_id(self, c):
        self._callid = c

    @property
    def read(self) -> List["Variable"]:
        return [self.argument]

    def set_type(self, t: ArgumentType):
        assert isinstance(t, ArgumentType)
        self._type = t

    def get_type(self) -> ArgumentType:
        return self._type

    def __str__(self):
        call_id = "none"
        if self.call_id:
            call_id = "(id ({}))".format(self.call_id)
        return "ARG_{} {} {}".format(self._type.name, str(self._argument), call_id)
