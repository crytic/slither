from .variable import Variable
from slither.core.children.child_contract import ChildContract

class StateVariable(ChildContract, Variable):


    @property
    def canonical_name(self):
        return '{}.{}'.format(self.contract.name, self.name)


