from typing import Optional, List

from slither.slithir.operations.operation import Operation


class Call(Operation):
    def __init__(self) -> None:
        super().__init__()
        self._arguments = []

    @property
    def arguments(self):
        return self._arguments

    @arguments.setter
    def arguments(self, v):
        self._arguments = v

    def can_reenter(self, _callstack: Optional[List] = None) -> bool:  # pylint: disable=no-self-use
        """
        Must be called after slithIR analysis pass
        :return: bool
        """
        return False

    def can_send_eth(self) -> bool:  # pylint: disable=no-self-use
        """
        Must be called after slithIR analysis pass
        :return: bool
        """
        return False
