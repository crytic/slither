from typing import Dict, TYPE_CHECKING, Set

from slither.utils.colors import green
from slither.slithir.operations.phi import Phi
from slither.core.variables.variable import Variable

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE, VALID_LVALUE
    from slither.core.cfg.node import Node


class PhiMemberMay(Phi):
    def __init__(
        self,
        left_variable: "VALID_LVALUE",
        base: Variable,
        nodes: Set["Node"],
        phi_info: Dict[Variable, Variable],
    ):
        super(PhiMemberMay, self).__init__(left_variable, nodes)
        self._phi_info = phi_info
        self._base = base

    @property
    def phi_info(self) -> Dict[Variable, Variable]:
        return self._phi_info

    @property
    def base(self) -> Variable:
        return self._base

    @property
    def read(self):
        raise Exception("Not implemented")

    def __str__(self):
        txt = []
        for key, item in self.phi_info.items():
            # items_txt = [f'{item}' for item in items]
            # txt.append(f'\t\t\t\t\t{key} :-> {items_txt}')
            txt = [f"{key} :-> {item}"]
        txt = ", ".join(txt)

        return green(f"{self.lvalue}({self.lvalue.type}) := \u03D5May({self.base}:{txt})")
