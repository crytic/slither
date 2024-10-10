from typing import Optional, TYPE_CHECKING

from slither.core.declarations.contract_level import ContractLevel
from slither.core.variables.variable import Variable

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.core.declarations import Contract


class StateVariable(ContractLevel, Variable):
    def __init__(self) -> None:
        super().__init__()
        self._node_initialization: Optional["Node"] = None
        self._location: Optional[str] = None

    def is_declared_by(self, contract: "Contract") -> bool:
        """
        Check if the element is declared by the contract
        :param contract:
        :return:
        """
        return self.contract == contract

    def set_location(self, loc: str) -> None:
        self._location = loc

    @property
    def location(self) -> Optional[str]:
        """
            Variable Location
            Can be default or transient
        Returns:
            (str)
        """
        return self._location

    @property
    def is_stored(self) -> bool:
        """
        Checks if the state variable is stored, based on it not being constant or immutable or transient.
        """
        return (
            not self._is_constant and not self._is_immutable and not self._location == "transient"
        )

    @property
    def is_transient(self) -> bool:
        """
        Checks if the state variable is transient. A transient variable can not be constant or immutable.
        """
        return self._location == "transient"

    # endregion
    ###################################################################################
    ###################################################################################
    # region Name
    ###################################################################################
    ###################################################################################

    @property
    def canonical_name(self) -> str:
        return f"{self.contract.name}.{self.name}"

    @property
    def full_name(self) -> str:
        """
        Return the name of the state variable as a function signaure
        str: func_name(type1,type2)
        :return: the function signature without the return values
        """
        name, parameters, _ = self.signature
        return name + "(" + ",".join(parameters) + ")"

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
