from typing import Optional, TYPE_CHECKING, List

from slither.slithir.operations.operation import Operation

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE
    from slither.slithir.operations.operation import OPERATION_READ_TYPE


class OperationWithLValue(Operation):
    """
        Operation with a lvalue
    """

    def __init__(self):
        super(OperationWithLValue, self).__init__()

        self._lvalue = None

    # Optional is needed for operations like call
    # When the return value is not assigned
    # Might be overriden in derived class
    # To remove Optional
    @property
    def lvalue(self) -> Optional["VALID_LVALUE"]:
        return self._lvalue

    @lvalue.setter
    def lvalue(self, lvalue):
        self._lvalue = lvalue

    @property
    def used(self) -> List["OPERATION_READ_TYPE"]:
        if self.lvalue:
            return self.read + [self.lvalue]
        else:
            return self.read
