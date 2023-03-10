from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.variables.temporary import TemporaryVariable


class TmpNewContract(OperationWithLValue):
    def __init__(self, contract_name: str, lvalue: TemporaryVariable) -> None:
        super().__init__()
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
        return f"{self.lvalue} = new {self.contract_name}"
