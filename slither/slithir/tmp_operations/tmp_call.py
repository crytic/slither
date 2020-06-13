from typing import Union, TYPE_CHECKING, Optional, List

from slither.core.declarations import (
    Event,
    Contract,
    SolidityVariableComposed,
    SolidityFunction,
    Structure,
)
from slither.core.variables.variable import Variable
from slither.slithir.operations import Operation
from slither.slithir.operations.lvalue import OperationWithLValue


if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE, VALID_RVALUE


class TmpCall(OperationWithLValue):
    def __init__(
        self,
        called: Union[
            Contract, Variable, SolidityVariableComposed, SolidityFunction, Structure, Event
        ],
        nbr_arguments: int,
        result: Optional["VALID_LVALUE"],
        type_call: str,
    ):
        assert isinstance(
            called,
            (Contract, Variable, SolidityVariableComposed, SolidityFunction, Structure, Event),
        )
        super(TmpCall, self).__init__()
        self._called = called
        self._nbr_arguments = nbr_arguments
        self._type_call = type_call
        self._lvalue = result
        self._ori: Optional[Operation] = None  #
        self._callid: Optional[str] = None
        self._gas: Optional["VALID_RVALUE"] = None
        self._value: Optional["VALID_RVALUE"] = None
        self._salt = None

    @property
    def call_value(self) -> Optional["VALID_RVALUE"]:
        return self._value

    @call_value.setter
    def call_value(self, v):
        self._value = v

    @property
    def call_gas(self) -> Optional["VALID_RVALUE"]:
        return self._gas

    @call_gas.setter
    def call_gas(self, gas):
        self._gas = gas

    @property
    def call_salt(self):
        return self._salt

    @call_salt.setter
    def call_salt(self, salt):
        self._salt = salt

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
        Union[Contract, Variable, SolidityVariableComposed, SolidityFunction, Structure, Event]
    ]:
        return [self.called]

    @property
    def called(
        self,
    ) -> Union[Contract, Variable, SolidityVariableComposed, SolidityFunction, Structure, Event]:
        return self._called

    @called.setter
    def called(
        self,
        c: Union[Contract, Variable, SolidityVariableComposed, SolidityFunction, Structure, Event],
    ):
        self._called = c

    @property
    def nbr_arguments(self) -> int:
        return self._nbr_arguments

    @property
    def type_call(self) -> str:
        return self._type_call

    @property
    def ori(self) -> Operation:
        return self._ori

    def set_ori(self, ori: Operation):
        self._ori = ori

    def __str__(self):
        return str(self.lvalue) + " = TMPCALL{} ".format(self.nbr_arguments) + str(self._called)
