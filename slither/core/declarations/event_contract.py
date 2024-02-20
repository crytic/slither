from typing import TYPE_CHECKING

from slither.core.declarations.contract_level import ContractLevel
from slither.core.declarations import Event

if TYPE_CHECKING:
    from slither.core.declarations import Contract


class EventContract(Event, ContractLevel):
    def is_declared_by(self, contract: "Contract") -> bool:
        """
        Check if the element is declared by the contract
        :param contract:
        :return:
        """
        return self.contract == contract

    @property
    def canonical_name(self) -> str:
        """Return the function signature as a str
        Returns:
            str: contract.func_name(type1,type2)
        """
        return self.contract.name + "." + self.full_name
