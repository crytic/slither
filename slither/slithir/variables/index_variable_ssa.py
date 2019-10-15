'''
    This class is used for the SSA version of slithIR
    It is similar to the non-SSA version of slithIR
    as the ReferenceVariable are in SSA form in both version
'''
from .index_variable import IndexVariable
from .variable import SlithIRVariable

class IndexVariableSSA(IndexVariable):

    def __init__(self, reference):
        super(IndexVariableSSA, self).__init__(reference.node, reference.index)

        self._non_ssa_version = reference

    @property
    def non_ssa_version(self):
        return self._non_ssa_version
