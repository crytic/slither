from typing import Optional, List, Union

from slither.core.declarations import Function
from slither.core.variables import Variable
from slither.slithir.operations.operation import Operation


class Call(Operation):
    def __init__(self, names: Optional[List[str]] = None) -> None:
        """
        #### Parameters
        names -
            For calls of the form f({argName1 : arg1, ...}), the names of parameters listed in call order.
            Otherwise, None.
        """
        assert (names is None) or isinstance(names, list)
        super().__init__()
        self._arguments: List[Variable] = []
        self._names = names

    @property
    def names(self) -> Optional[List[str]]:
        """
        For calls of the form f({argName1 : arg1, ...}), the names of parameters listed in call order.
        Otherwise, None.
        """
        return self._names

    @property
    def arguments(self) -> List[Variable]:
        return self._arguments

    @arguments.setter
    def arguments(self, v: List[Variable]) -> None:
        self._arguments = v

    # pylint: disable=no-self-use
    def can_reenter(self, _callstack: Optional[List[Union[Function, Variable]]] = None) -> bool:
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
