from typing import TYPE_CHECKING

from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.variables.temporary import TemporaryVariable

if TYPE_CHECKING:
    from slither.core.solidity_types.user_defined_type import UserDefinedType


class TmpNewContract(OperationWithLValue):
    def __init__(
        self, contract_type: "UserDefinedType", lvalue: TemporaryVariable
    ) -> None:
        super().__init__()
        self._contract_type: "UserDefinedType" = contract_type
        self._lvalue = lvalue
        self._call_value = None
        self._call_salt = None

    @property
    def contract_name(self) -> str:
        """Return the name of the contract being created."""
        return self._contract_type.type.name

    @property
    def contract_type(self) -> "UserDefinedType":
        """Return the UserDefinedType of the contract being created."""
        return self._contract_type

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
