from typing import TYPE_CHECKING, Set, List

from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue
from slither.utils.colors import green

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE, VALID_RVALUE
    from slither.core.cfg.node import Node


class Phi(OperationWithLValue):
    def __init__(self, left_variable: "VALID_LVALUE", nodes: Set["Node"]):
        # When Phi operations are created the
        # correct indexes of the variables are not yet computed
        # We store the nodes where the variables are written
        # so we can update the rvalues of the Phi operation
        # after its instantiation
        assert is_valid_lvalue(left_variable)
        assert isinstance(nodes, set)
        super(Phi, self).__init__()
        self._lvalue = left_variable
        self._rvalues: List["VALID_RVALUE"] = []
        self._nodes: Set["Node"] = nodes

    @property
    def read(self) -> List["VALID_RVALUE"]:
        return self.rvalues

    @property
    def rvalues(self) -> List["VALID_RVALUE"]:
        return self._rvalues

    @rvalues.setter
    def rvalues(self, vals: List["VALID_RVALUE"]):
        self._rvalues = vals

    @property
    def lvalue(self) -> "VALID_LVALUE":
        return self._lvalue

    @lvalue.setter
    def lvalue(self, lvalue):
        self._lvalue = lvalue

    @property
    def nodes(self) -> Set["Node"]:
        return self._nodes

    def __str__(self):
        return green(
            "{}({}) ?= \u03D5({})".format(
                self.lvalue, self.lvalue.type, [str(v) for v in self._rvalues]
            )
        )
