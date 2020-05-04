from typing import TYPE_CHECKING

from slither.slithir.variables.reference import ReferenceVariable
from slither.core.declarations import Function


if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.slithir.variables.variable import SlithIRVariable

class IndexVariable(ReferenceVariable):
    COUNTER = 0

    def __init__(self, node: "Node", base: "SlithIRVariable", offset: "SlithIRVariable", index=None):
        super(IndexVariable, self).__init__()
        self._index: int
        if index is None:
            self._index = IndexVariable.COUNTER
            IndexVariable.COUNTER += 1
        else:
            self._index = index
        self._node: "Node" = node

        self._base: "SlithIRVariable" = base
        self._offset: "SlithIRVariable" = offset

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def offset(self) -> "SlithIRVariable":
        return self._offset

    @offset.setter
    def offset(self, offset):
        self._offset = offset

    @property
    def base(self) -> "SlithIRVariable":
        return self._base

    @base.setter
    def base(self, base):
        self._base = base

    @property
    def name(self) -> str:
        return "INDEX_{}".format(self.index)

    @name.setter
    def name(self, name):
        self._name = name

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
