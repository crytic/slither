from typing import Optional, TYPE_CHECKING

from slither.slithir.operations.lvalue import OperationWithLValue

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE


class TmpNewContract(OperationWithLValue):
    def __init__(self, contract_name: str, lvalue: Optional["VALID_LVALUE"]):
        super(TmpNewContract, self).__init__()
        self._contract_name = contract_name
        self._lvalue = lvalue
        self._call_value = None
        self._call_salt = None

    @property
    def contract_name(self) -> str:
        return self._contract_name

    @property
    def call_value(self):
        return self._call_value

    @call_value.setter
    def call_value(self, v):
        self._call_value = v

    @property
    def call_salt(self):
        return self._call_salt

    @call_salt.setter
    def call_salt(self, s):
        self._call_salt = s

    @property
    def read(self):
        return []

    def __str__(self):
        return "{} = new {}".format(self.lvalue, self.contract_name)
