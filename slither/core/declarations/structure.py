from slither.core.sourceMapping.sourceMapping import SourceMapping
from slither.core.children.childContract import ChildContract

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

    def __str__(self):
        return self.name
