from typing import List, Set, Union, TYPE_CHECKING
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue
from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.slithir.variables.local_variable import LocalIRVariable
from slither.slithir.variables.state_variable import StateIRVariable
from slither.slithir.variables.temporary_ssa import TemporaryVariableSSA

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class Phi(OperationWithLValue):
    def __init__(
        self, left_variable: Union[LocalIRVariable, StateIRVariable], nodes: Set["Node"]
    ) -> None:
        # When Phi operations are created the
        # correct indexes of the variables are not yet computed
        # We store the nodes where the variables are written
        # so we can update the rvalues of the Phi operation
        # after its instantiation
        assert is_valid_lvalue(left_variable)
        assert isinstance(nodes, set)
        super().__init__()
        self._lvalue = left_variable
        self._rvalues = []
        self._nodes = nodes

    @property
    def read(
        self,
    ) -> List[
        Union[SolidityVariableComposed, LocalIRVariable, TemporaryVariableSSA, StateIRVariable]
    ]:
        return self.rvalues

    @property
    def rvalues(self):
        return self._rvalues

    @rvalues.setter
    def rvalues(self, vals):
        self._rvalues = vals

    @property
    def nodes(self) -> Set["Node"]:
        return self._nodes

    def __str__(self):
        return f"{self.lvalue}({self.lvalue.type}) := \u03D5({[str(v) for v in self._rvalues]})"
