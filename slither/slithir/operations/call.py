
from slither.slithir.operations.operation import Operation

class Call(Operation):

    def __init__(self):
        super(Call, self).__init__()
        self._arguments = []

    @property
    def arguments(self):
        return self._arguments

    @arguments.setter
    def arguments(self, v):
        self._arguments = v

    # if array inside the parameters
    def _unroll(self, l):
        ret = []
        for x in l:
            if not isinstance(x, list):
                ret += [x]
            else:
                ret += self._unroll(x)
        return ret
