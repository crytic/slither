'''
    This class is used for the SSA version of slithIR
    It is similar to the non-SSA version of slithIR
    as the TemporaryVariable are in SSA form in both version
'''
from .temporary import TemporaryVariable
from .variable import SlithIRVariable

class TemporaryVariableSSA(TemporaryVariable):

    def __init__(self, temporary):
        super(TemporaryVariableSSA, self).__init__(temporary.node, temporary.index)

        self._non_ssa_version = temporary


    @property
    def non_ssa_version(self):
        return self._non_ssa_version

