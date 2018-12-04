import logging

from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.slithir.variables import TupleVariable
from slither.core.declarations.function import Function
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue

class Phi(OperationWithLValue):

    def __init__(self, left_variable, nodes):
        # When Phi operations are created the
        # correct indexes of the variables are not yet computed
        # We store the nodes where the variables are written 
        # so we can update the rvalues of the Phi operation
        # after its instantiation
        assert is_valid_lvalue(left_variable)
        assert isinstance(nodes, set)
        super(Phi, self).__init__()
        self._lvalue = left_variable
        self._rvalues = []
        self._nodes = nodes

    @property
    def read(self):
        return [self.rvalues]

    @property
    def rvalues(self):
        return self._rvalues

    @rvalues.setter
    def rvalues(self, vals):
        self._rvalues = vals

    @property
    def nodes(self):
        return self._nodes
    def __str__(self):
        return '{}({}) := \u03D5({})'.format(self.lvalue, self.lvalue.type, [v.ssa_name for v in self._rvalues])
