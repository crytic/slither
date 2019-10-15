from .phi import Phi
from slither.utils.colors import green
class PhiScalar(Phi):

    def __str__(self):
        return green('{}({}) := \u03D5({})'.format(self.lvalue, self.lvalue.type, [str(v) for v in self._rvalues]))
