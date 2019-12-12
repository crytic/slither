from .reference import ReferenceVariable
from slither.core.declarations import Function


class IndexVariable(ReferenceVariable):
    COUNTER = 0

    def __init__(self, node, base, offset, index=None):
        super(IndexVariable, self).__init__()
        if index is None:
            self._index = IndexVariable.COUNTER
            IndexVariable.COUNTER += 1
        else:
            self._index = index
        self._node = node

        self._base = base
        self._offset = offset


    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, offset):
        self._offset = offset

    @property
    def base(self):
        return self._base

    @base.setter
    def base(self, base):
        self._base = base

    @property
    def name(self):
        return 'INDEX_{}'.format(self.index)

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