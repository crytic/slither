import logging
from .expression import Expression
from slither.core.solidityTypes.type import Type

logger = logging.getLogger("NewArray")

class NewArray(Expression):

    # note: dont conserve the size of the array if provided
    def __init__(self, depth, array_type):
        super(NewArray, self).__init__()
        assert isinstance(array_type, Type)
        self._depth = depth
        self._array_type = array_type

    @property
    def array_type(self):
        return self._array_type

    @property
    def depth(self):
        return self._depth

    def __str__(self):
        return 'new ' + str(self._array_type) + '[]'* self._depth

