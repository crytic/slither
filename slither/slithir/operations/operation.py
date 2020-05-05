import abc
from typing import List, TYPE_CHECKING, Union, Any

from slither.core.context.context import Context
from slither.core.children.child_expression import ChildExpression
from slither.core.children.child_node import ChildNode
from slither.utils.utils import unroll

if TYPE_CHECKING:
    # TODO: Find a better design to enforce that SSA oeprations dont have localVariable/StateVariable
    from slither.core.variables.local_variable import LocalVariable  # For non-ssa operation
    from slither.core.variables.state_variable import StateVariable  # For non-ssa operation
    from slither.core.declarations import Function, SolidityVariable  # IR Assignement
    from slither.slithir.variables import TupleVariable  # IR Assignement
    from slither.slithir.utils.utils import VALID_RVALUE, VALID_LVALUE
    from slither.core.variables.local_variable import LocalVariable
    from slither.core.variables.state_variable import StateVariable

OPERATION_READ_TYPE = Union[
    "VALID_RVALUE",
    "VALID_LVALUE",
    "Function",
    "TupleVariable",
    "StateVariable",
    "LocalVariable",
    "SolidityVariable"
]


class AbstractOperation(abc.ABC):
    @property
    @abc.abstractmethod
    def read(self) -> List[OPERATION_READ_TYPE]:
        """
            Return the list of variables READ
        """
        pass

    @property
    @abc.abstractmethod
    def used(self) -> List[OPERATION_READ_TYPE]:
        """
            Return the list of variables used
        """
        pass


class Operation(Context, ChildExpression, ChildNode, AbstractOperation):
    @property
    def used(self) -> List[OPERATION_READ_TYPE]:
        """
            By default used is all the variables read
        """
        return self.read

    # if array inside the parameters
    @staticmethod
    def _unroll(list_to_unroll: List) -> List:
        return unroll(list_to_unroll)
