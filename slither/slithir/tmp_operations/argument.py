from enum import Enum
from typing import TYPE_CHECKING, Optional, List, Union

from slither.core.declarations import SolidityVariable
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations.operation import Operation
from slither.slithir.variables import TemporaryVariable, Constant, IndexVariable, MemberVariable

if TYPE_CHECKING:
    from slither.core.variables.variable import Variable


class ArgumentType(Enum):
    CALL = 0
    VALUE = 1
    GAS = 2
    DATA = 3


class Argument(Operation):
    def __init__(
        self,
        argument: Union[
            StateVariable,
            LocalVariable,
            TemporaryVariable,
            Constant,
            SolidityVariable,
            IndexVariable,
            MemberVariable,
        ],
    ):
        super(Argument, self).__init__()
        assert isinstance(
            argument,
            (
                StateVariable,
                LocalVariable,
                TemporaryVariable,
                Constant,
                SolidityVariable,
                IndexVariable,
                MemberVariable,
            ),
        )
        self._argument = argument
        self._type = ArgumentType.CALL
        self._callid: Optional[str] = None  # only used if gas/value != 0

    @property
    def argument(
        self,
    ) -> Union[
        StateVariable,
        LocalVariable,
        TemporaryVariable,
        Constant,
        SolidityVariable,
        IndexVariable,
        MemberVariable,
    ]:
        return self._argument

    @property
    def call_id(self) -> Optional[str]:
        return self._callid

    @call_id.setter
    def call_id(self, c):
        self._callid = c

    @property
    def read(
        self,
    ) -> List[
        Union[
            StateVariable,
            LocalVariable,
            TemporaryVariable,
            Constant,
            SolidityVariable,
            IndexVariable,
            MemberVariable,
        ]
    ]:
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
