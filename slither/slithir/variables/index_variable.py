from .reference import ReferenceVariable
from slither.core.declarations import Function


class IndexVariable(ReferenceVariable):
    COUNTER = 0

    def __init__(self, node, index=None):
        super(IndexVariable, self).__init__()
        if index is None:
            self._index = IndexVariable.COUNTER
            IndexVariable.COUNTER += 1
        else:
            self._index = index
        self._points_to = None
        self._node = node



    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def name(self):
        return 'REF_{}'.format(self.index)

    # overide of core.variables.variables
    # reference can have Function has a type
    # to handle the function selector
    def set_type(self, t):
        if not isinstance(t, Function):
            super(ReferenceVariable, self).set_type(t)
        else:
            self._type = t

    def __str__(self):
        return self.name