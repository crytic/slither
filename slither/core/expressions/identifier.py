from typing import TYPE_CHECKING, Optional, Union

from slither.core.declarations.contract_level import ContractLevel
from slither.core.declarations.top_level import TopLevel
from slither.core.expressions.expression import Expression
from slither.core.variables.variable import Variable


if TYPE_CHECKING:
    from slither.core.solidity_types.type import Type
    from slither.core.declarations import Contract, SolidityVariable, SolidityFunction
    from slither.solc_parsing.yul.evm_functions import YulBuiltin


class Identifier(Expression):
    def __init__(
        self,
        value: Union[
            Variable,
            "TopLevel",
            "ContractLevel",
            "Contract",
            "SolidityVariable",
            "SolidityFunction",
            "YulBuiltin",
        ],
    ) -> None:
        super().__init__()
        # pylint: disable=import-outside-toplevel
        from slither.core.declarations import Contract, SolidityVariable, SolidityFunction
        from slither.solc_parsing.yul.evm_functions import YulBuiltin

        assert isinstance(
            value,
            (
                Variable,
                TopLevel,
                ContractLevel,
                Contract,
                SolidityVariable,
                SolidityFunction,
                YulBuiltin,
            ),
        )

        self._value: Union[
            Variable,
            "TopLevel",
            "ContractLevel",
            "Contract",
            "SolidityVariable",
            "SolidityFunction",
            "YulBuiltin",
        ] = value
        self._type: Optional["Type"] = None

    @property
    def type(self) -> Optional["Type"]:
        return self._type

    @type.setter
    def type(self, new_type: "Type") -> None:
        self._type = new_type

    @property
    def value(
        self,
    ) -> Union[
        Variable,
        "TopLevel",
        "ContractLevel",
        "Contract",
        "SolidityVariable",
        "SolidityFunction",
        "YulBuiltin",
    ]:
        return self._value

    def __str__(self) -> str:
        return str(self._value)
