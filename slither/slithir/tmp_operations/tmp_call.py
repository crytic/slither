from typing import List, Optional, Union

from slither.core.declarations import (
    Event,
    Contract,
    SolidityVariableComposed,
    SolidityFunction,
    Structure,
)
from slither.core.declarations.custom_error import CustomError
from slither.core.variables.variable import Variable
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.slithir.operations.member import Member
from slither.slithir.tmp_operations.tmp_new_array import TmpNewArray
from slither.slithir.tmp_operations.tmp_new_contract import TmpNewContract
from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.tuple import TupleVariable


class TmpCall(OperationWithLValue):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        called: SourceMapping,
        nbr_arguments: int,
        result: Union[TupleVariable, TemporaryVariable],
        type_call: str,
        names: Optional[List[str]] = None,
    ) -> None:
        # pylint: disable=too-many-arguments
        """
        #### Parameters
        names -
            For calls of the form f({argName1 : arg1, ...}), the names of parameters listed in call order.
            Otherwise, None.
        """
        assert isinstance(
            called,
            (
                Contract,
                Variable,
                SolidityVariableComposed,
                SolidityFunction,
                Structure,
                Event,
                CustomError,
            ),
        )
        super().__init__()
        self._called = called
        self._nbr_arguments = nbr_arguments
        self._type_call = type_call
        self._names = names
        self._lvalue = result
        self._ori = None  #
        self._callid = None
        self._gas = None
        self._value = None
        self._salt = None

    @property
    def names(self) -> Optional[List[str]]:
        """
        For calls of the form f({argName1 : arg1, ...}), the names of parameters listed in call order.
        Otherwise, None.
        """
        return self._names

    @property
    def call_value(self):
        return self._value

    @call_value.setter
    def call_value(self, v):
        self._value = v

    @property
    def call_gas(self):
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
    def call_id(self):
        return self._callid

    @call_id.setter
    def call_id(self, c):
        self._callid = c

    @property
    def read(self):
        return [self.called]

    @property
    def called(self):
        return self._called

    @called.setter
    def called(self, c):
        self._called = c

    @property
    def nbr_arguments(self) -> int:
        return self._nbr_arguments

    @property
    def type_call(self) -> str:
        return self._type_call

    @property
    def ori(self) -> Optional[Union[TmpNewContract, TmpNewArray, "TmpCall", Member]]:
        return self._ori

    def set_ori(self, ori: Union["TmpCall", TmpNewContract, TmpNewArray, Member]) -> None:
        self._ori = ori

    def __str__(self):
        return str(self.lvalue) + f" = TMPCALL{self.nbr_arguments} " + str(self._called)
