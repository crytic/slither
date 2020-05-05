from typing import TYPE_CHECKING, List, Union

from slither.slithir.operations.operation import Operation

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE

# Recursive type not handled by mypy
# https://github.com/python/mypy/issues/731
# RecList = List[Union["RecList", "VALID_RVALUE"]]
RecList = List[Union[List, "VALID_RVALUE"]]


class Call(Operation):
    def __init__(self):
        super(Call, self).__init__()
        # TODO determine types
        self._arguments: RecList = []

    @property
    def arguments(self) -> RecList:
        return self._arguments

    @arguments.setter
    def arguments(self, v: RecList):
        self._arguments = v

    def can_reenter(self, callstack=None) -> bool:
        """
        Must be called after slithIR analysis pass
        :return: bool
        """
        return False

    def can_send_eth(self) -> bool:
        """
        Must be called after slithIR analysis pass
        :return: bool
        """
        return False
