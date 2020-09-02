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

    def can_reenter(self, _callstack=None):  # pylint: disable=no-self-use
        """
        Must be called after slithIR analysis pass
        :return: bool
        """
        return False

    def can_send_eth(self):  # pylint: disable=no-self-use
        """
        Must be called after slithIR analysis pass
        :return: bool
        """
        return False
