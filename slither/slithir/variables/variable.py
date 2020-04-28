from collections import defaultdict
from slither.core.declarations import Structure
from slither.core.solidity_types import UserDefinedType
from slither.core.variables.variable import Variable


class SlithIRVariable(Variable):
    def __init__(self):
        super(SlithIRVariable, self).__init__()
        self._index = 0
        self._ssa_phi_info = defaultdict(list)

    @property
    def ssa_name(self):
        return self.name

    @property
    def ssa_phi_info(self):
        return self._ssa_phi_info

    def generate_ssa_phi_info(self):
        return
        # from slither.slithir.variables import Constant
        # if isinstance(self.type, UserDefinedType):
        #     if isinstance(self.type.type, Structure):
        #         for member in self.type.type.elems.keys():
        #             self._ssa_phi_info[member] = [Constant("0")]

    def __str__(self):
        return self.ssa_name
