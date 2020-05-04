from typing import TYPE_CHECKING, Optional

from slither.slithir.variables.reference import ReferenceVariable

if TYPE_CHECKING:
    from slither.slithir.variables.variable import SlithIRVariable
    from slither.core.cfg.node import Node


class MemberVariable(ReferenceVariable):
    COUNTER = 0

    def __init__(self, node: "Node", base: "SlithIRVariable", member: str, index: Optional[int] = None):
        super(MemberVariable, self).__init__()
        self._index: int
        if index is None:
            self._index = MemberVariable.COUNTER
            MemberVariable.COUNTER += 1
        else:
            self._index = index

        self._node: "Node" = node
        self._member: str = member
        self._base: "SlithIRVariable"= base

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def member(self) -> str:
        return self._member

    @member.setter
    def member(self, member):
        self._member = member

    @property
    def base(self) -> "SlithIRVariable":
        return self._base

    @base.setter
    def base(self, base):
        self._base = base

    @property
    def name(self) -> str:
        return "MEMBER_{}".format(self.index)

    @name.setter
    def name(self, name):
        self._name = name

    def __str__(self):
        return self.name
