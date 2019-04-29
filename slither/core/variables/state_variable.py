from .variable import Variable
from slither.core.children.child_contract import ChildContract

class StateVariable(ChildContract, Variable):

    def is_declared_by(self, contract):
        """
        Check if the element is declared by the contract
        :param contract:
        :return:
        """
        return self.contract == contract

    @property
    def canonical_name(self):
        return '{}.{}'.format(self.contract.name, self.name)


