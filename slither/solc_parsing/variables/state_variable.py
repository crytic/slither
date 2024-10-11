from typing import Dict

from slither.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from slither.core.variables.state_variable import StateVariable


class StateVariableSolc(VariableDeclarationSolc):
    def __init__(self, variable: StateVariable, variable_data: Dict) -> None:
        super().__init__(variable, variable_data)

    @property
    def underlying_variable(self) -> StateVariable:
        # Todo: Not sure how to overcome this with mypy
        assert isinstance(self._variable, StateVariable)
        return self._variable

    def _analyze_variable_attributes(self, attributes: Dict) -> None:
        """
        Variable Location
        Can be default or transient
        """
        if "storageLocation" in attributes:
            self.underlying_variable.set_location(attributes["storageLocation"])
        else:
            # We don't have to support legacy ast
            # as transient location was added in 0.8.28
            # and we know it must be default
            self.underlying_variable.set_location("default")

        super()._analyze_variable_attributes(attributes)
