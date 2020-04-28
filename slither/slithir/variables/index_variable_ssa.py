"""
    This class is used for the SSA version of slithIR
    It is similar to the non-SSA version of slithIR
    as the ReferenceVariable are in SSA form in both version
"""
from .index_variable import IndexVariable
from .variable import SlithIRVariable


class IndexVariableSSA(IndexVariable):
    def __init__(self, reference):
        super(IndexVariableSSA, self).__init__(
            reference.node, reference.base, reference.offset, index=reference.index
        )

        self._non_ssa_version = reference
        self._index_ssa = 0

    @property
    def index_ssa(self):
        return self._index_ssa

    @index_ssa.setter
    def index_ssa(self, index_ssa):
        self._index_ssa = index_ssa

    @property
    def non_ssa_version(self):
        return self._non_ssa_version

    @property
    def name(self):
        return "INDEX_{}_{}".format(self.index, self.index_ssa)
