import abc
from typing import Any, List
from slither.core.context.context import Context
from slither.core.children.child_expression import ChildExpression
from slither.core.children.child_node import ChildNode
from slither.core.variables.variable import Variable
from slither.utils.utils import unroll


class AbstractOperation(abc.ABC):
    @property
    @abc.abstractmethod
    def read(self):
        """
        Return the list of variables READ
        """
        pass  # pylint: disable=unnecessary-pass

    @property
    @abc.abstractmethod
    def used(self):
        """
        Return the list of variables used
        """
        pass  # pylint: disable=unnecessary-pass


class Operation(Context, ChildExpression, ChildNode, AbstractOperation):
    @property
    def used(self) -> List[Variable]:
        """
        By default used is all the variables read
        """
        return self.read

    # if array inside the parameters
    @staticmethod
    def _unroll(l: List[Any]) -> List[Any]:
        return unroll(l)
