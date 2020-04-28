"""
    This class is used for the SSA version of slithIR
    It is similar to the non-SSA version of slithIR
    as the TupleVariable are in SSA form in both version
"""
from .tuple import TupleVariable
from .variable import SlithIRVariable


class TupleVariableSSA(TupleVariable):
    def __init__(self, t):
        super(TupleVariableSSA, self).__init__(t.node, t.index)

        self._non_ssa_version = t

    @property
    def non_ssa_version(self):
        return self._non_ssa_version
