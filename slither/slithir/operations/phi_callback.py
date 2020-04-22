from collections import namedtuple
from typing import Optional, List

from slither.slithir.utils.utils import is_valid_lvalue
from .phi import Phi


class PhiCallback(Phi):

    def __init__(self, left_variable, nodes, call_ir, rvalue, storage_idx: List[int]):
        assert is_valid_lvalue(left_variable)
        assert isinstance(nodes, set)
        super(PhiCallback, self).__init__(left_variable, nodes)
        self._call_ir = call_ir
        self._rvalues = [rvalue]
        self._rvalue_no_callback = rvalue
        self._storage_idx = storage_idx

    @property
    def callee_ir(self):
        return self._call_ir

    @property
    def read(self):
        return self.rvalues

    @property
    def storage_idx(self) -> List[int]:
        """
        Return the list of idx where the variable is used as as torage parameter in the ir.
        :return:
        """
        return self._storage_idx

    @property
    def rvalues(self):
        return self._rvalues

    @property
    def rvalue_no_callback(self):
        '''
            rvalue if callback are not considered
        '''
        return self._rvalue_no_callback

    @rvalues.setter
    def rvalues(self, vals):
        self._rvalues = vals

    @property
    def nodes(self):
        return self._nodes

    def __str__(self):
        return '{}({}) := \u03D5({})'.format(self.lvalue, self.lvalue.type, [v.ssa_name for v in self._rvalues])
