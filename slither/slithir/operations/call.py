from slither.core.declarations import Function
from slither.core.variables import Variable
from slither.slithir.operations.operation import Operation


class Call(Operation):
    def __init__(self, names: list[str] | None = None) -> None:
        """
        #### Parameters
        names -
            For calls of the form f({argName1 : arg1, ...}), the names of parameters listed in call order.
            Otherwise, None.
        """
        assert (names is None) or isinstance(names, list)
        super().__init__()
        self._arguments: list[Variable] = []
        self._names = names

    @property
    def names(self) -> list[str] | None:
        """
        For calls of the form f({argName1 : arg1, ...}), the names of parameters listed in call order.
        Otherwise, None.
        """
        return self._names

    @property
    def arguments(self) -> list[Variable]:
        return self._arguments

    @arguments.setter
    def arguments(self, v: list[Variable]) -> None:
        self._arguments = v

    def can_reenter(self, _callstack: list[Function | Variable] | None = None) -> bool:
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
