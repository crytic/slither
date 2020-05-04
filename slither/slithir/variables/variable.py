from typing import Dict, TYPE_CHECKING

from slither.core.variables.variable import Variable



class SlithIRVariable(Variable):
    def __init__(self):
        super(SlithIRVariable, self).__init__()
        self._index = 0
        self._ssa_phi_info: Dict["SlithIRVariable", "SlithIRVariable"] = dict() #defaultdict(list)

    @property
    def ssa_name(self) -> str:
        return self.name

    @property
    def ssa_phi_info(self) -> Dict["SlithIRVariable", "SlithIRVariable"]:
        return self._ssa_phi_info

    def __str__(self):
        return self.ssa_name
