from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.children.child_contract import ChildContract

from slither.core.variables.variable import Variable

class Structure(ChildContract, SourceMapping):

    def __init__(self):
        super(Structure, self).__init__()
        self._name = None
        self._canonical_name = None
        self._elems = None

    @property
    def canonical_name(self):
        return self._canonical_name

    @property
    def name(self):
        return self._name

    @property
    def elems(self):
        return self._elems

    def is_declared_by(self, contract):
        """
        Check if the element is declared by the contract
        :param contract:
        :return:
        """
        return self.contract == contract

    def __str__(self):
        return self.name
