from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.solidity_types.elementary_type import ElementaryType


class TmpNewElementaryType(OperationWithLValue):
    def __init__(self, new_type, lvalue):
        assert isinstance(new_type, ElementaryType)
        super(TmpNewElementaryType, self).__init__()
        self._type = new_type
        self._lvalue = lvalue

    @property
    def read(self):
        return []

    @property
    def type(self):
        return self._type

    def __str__(self):
        return "{} = new {}".format(self.lvalue, self._type)
