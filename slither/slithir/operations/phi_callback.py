from typing import List, TYPE_CHECKING, Set, Union

from slither.slithir.operations.phi import Phi
from slither.slithir.utils.utils import is_valid_lvalue

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE, VALID_RVALUE
    from slither.core.cfg.node import Node
    from slither.slithir.operations import (
        InternalCall,
        HighLevelCall,
        InternalDynamicCall,
        LowLevelCall,
    )
    from ..variables import StateIRVariable


class PhiCallback(Phi):
    def __init__(
        self,
        left_variable: "VALID_LVALUE",
        nodes: Set["Node"],
        call_ir: Union["InternalCall", "HighLevelCall", "InternalDynamicCall", "LowLevelCall"],
        rvalue: "StateIRVariable",
        storage_idx: List[int],
    ):
        assert is_valid_lvalue(left_variable)
        assert isinstance(nodes, set)
        super(PhiCallback, self).__init__(left_variable, nodes)
        self._call_ir = call_ir
        self._rvalues: List["VALID_RVALUE"] = [rvalue]
        self._rvalue_no_callback = rvalue
        self._storage_idx: List[int] = storage_idx

    @property
    def callee_ir(
        self,
    ) -> Union["InternalCall", "HighLevelCall", "InternalDynamicCall", "LowLevelCall"]:
        return self._call_ir

    @property
    def read(self) -> List["VALID_RVALUE"]:
        return self.rvalues

    @property
    def storage_idx(self) -> List[int]:
        """
        Return the list of idx where the variable is used as a storage parameter in the ir.
        :return:
        """
        return self._storage_idx

    @property
    def rvalues(self) -> List["VALID_RVALUE"]:
        return self._rvalues

    @property
    def rvalue_no_callback(self) -> "StateIRVariable":
        """
            rvalue if callback are not considered
        """
        return self._rvalue_no_callback

    @rvalues.setter
    def rvalues(self, vals: List["VALID_RVALUE"]):
        self._rvalues = vals

    @property
    def nodes(self) -> Set["Node"]:
        return self._nodes

    def __str__(self):
        return "{}({}) := \u03D5({})".format(
            self.lvalue, self.lvalue.type, [v.ssa_name for v in self._rvalues]
        )
