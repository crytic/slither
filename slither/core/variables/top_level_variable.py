from typing import Optional, TYPE_CHECKING, Tuple, List

from slither.core.declarations.top_level import TopLevel
from slither.core.variables.variable import Variable
from slither.core.children.child_contract import ChildContract
from slither.utils.type import export_nested_types_from_variable

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.core.declarations import Contract


class TopLevelVariable(TopLevel, Variable):
    def __init__(self):
        super().__init__()
        self._node_initialization: Optional["Node"] = None

    # endregion
    ###################################################################################
    ###################################################################################
    # region IRs (initialization)
    ###################################################################################
    ###################################################################################

    @property
    def node_initialization(self) -> Optional["Node"]:
        """
        Node for the state variable initalization
        :return:
        """
        return self._node_initialization

    @node_initialization.setter
    def node_initialization(self, node_initialization):
        self._node_initialization = node_initialization

    # endregion
    ###################################################################################
    ###################################################################################
