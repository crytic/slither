from typing import TYPE_CHECKING
from slither.core.declarations.contract_level import ContractLevel


from slither.core.declarations.custom_error import CustomError

if TYPE_CHECKING:
    from slither.core.declarations import Contract


class CustomErrorContract(CustomError, ContractLevel):
    def is_declared_by(self, contract: "Contract") -> bool:
        """
        Check if the element is declared by the contract
        :param contract:
        :return:
        """
        return self.contract == contract

    @property
    def canonical_name(self) -> str:
        return self.contract.name + "." + self.full_name
