from typing import Dict

from slither.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from slither.core.variables.local_variable import LocalVariable


class LocalVariableSolc(VariableDeclarationSolc):
    def __init__(self, variable: LocalVariable, variable_data: Dict) -> None:
        super().__init__(variable, variable_data)

    @property
    def underlying_variable(self) -> LocalVariable:
        # Todo: Not sure how to overcome this with mypy
        assert isinstance(self._variable, LocalVariable)
        return self._variable

    def _analyze_variable_attributes(self, attributes: Dict) -> None:
        """'
        Variable Location
        Can be storage/memory or default
        """
        if "storageLocation" in attributes:
            location = attributes["storageLocation"]
            self.underlying_variable.set_location(location)
        else:
            if "memory" in attributes["type"]:
                self.underlying_variable.set_location("memory")
            elif "storage" in attributes["type"]:
                self.underlying_variable.set_location("storage")
            else:
                self.underlying_variable.set_location("default")

        super()._analyze_variable_attributes(attributes)
