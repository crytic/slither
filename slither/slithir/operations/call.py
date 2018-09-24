
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

