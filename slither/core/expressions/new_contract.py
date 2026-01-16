from __future__ import annotations

from typing import TYPE_CHECKING

from slither.core.expressions.expression import Expression

if TYPE_CHECKING:
    from slither.core.solidity_types.user_defined_type import UserDefinedType


class NewContract(Expression):
    def __init__(self, contract_type: UserDefinedType) -> None:
        super().__init__()
        self._contract_type: UserDefinedType = contract_type
        self._gas = None
        self._value = None
        self._salt = None

    @property
    def contract_name(self) -> str:
        """Return the name of the contract being created."""
        return self._contract_type.type.name

    @property
    def contract_type(self) -> UserDefinedType:
        """Return the UserDefinedType of the contract being created."""
        return self._contract_type

    @property
    def call_value(self):
        return self._value

    @call_value.setter
    def call_value(self, v):
        self._value = v

    @property
    def call_salt(self):
        return self._salt

    @call_salt.setter
    def call_salt(self, salt):
        self._salt = salt

    def __str__(self) -> str:
        return "new " + self.contract_name
