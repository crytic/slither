from slither.core.sourceMapping.sourceMapping import SourceMapping
from slither.core.children.childContract import ChildContract

class Enum(ChildContract, SourceMapping):
    def __init__(self, name, canonical_name, values):
        self._name = name
        self._canonical_name = canonical_name
        self._values = values

    @property
    def canonical_name(self):
        return self._canonical_name

    @property
    def name(self):
        return self._name

    @property
    def values(self):
        return self._values

