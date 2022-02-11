from slither.core.children.child_contract import ChildContract
from slither.core.declarations.custom_error import CustomError


class CustomErrorContract(CustomError, ChildContract):
    def is_declared_by(self, contract):
        """
        Check if the element is declared by the contract
        :param contract:
        :return:
        """
        return self.contract == contract
