from typing import Dict

from slither.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from slither.core.variables.local_variable_init_from_tuple import LocalVariableInitFromTuple
from slither.core.variables.variable import VariableLocation


class LocalVariableInitFromTupleSolc(VariableDeclarationSolc):
    def __init__(
        self, variable: LocalVariableInitFromTuple, variable_data: Dict, index: int
    ) -> None:
        super().__init__(variable, variable_data)
        variable.tuple_index = index

    @property
    def underlying_variable(self) -> LocalVariableInitFromTuple:
        # Todo: Not sure how to overcome this with mypy
        assert isinstance(self._variable, LocalVariableInitFromTuple)
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
                self.underlying_variable.set_location(VariableLocation.MEMORY)
            elif "storage" in attributes["type"]:
                self.underlying_variable.set_location(VariableLocation.STORAGE)
            else:
                self.underlying_variable.set_location(VariableLocation.DEFAULT)

        super()._analyze_variable_attributes(attributes)
