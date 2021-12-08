from typing import List, TYPE_CHECKING, Optional, Type, Union

from slither.core.solidity_types import UserDefinedType
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.local_variable import LocalVariable

if TYPE_CHECKING:
    from slither.core.compilation_unit import SlitherCompilationUnit


class CustomError(SourceMapping):
    def __init__(self, compilation_unit: "SlitherCompilationUnit"):
        super().__init__()
        self._name: str = ""
        self._parameters: List[LocalVariable] = []
        self._compilation_unit = compilation_unit

        self._solidity_signature: Optional[str] = None

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = new_name

    @property
    def parameters(self) -> List[LocalVariable]:
        return self._parameters

    def add_parameters(self, p: "LocalVariable"):
        self._parameters.append(p)

    @property
    def compilation_unit(self) -> "SlitherCompilationUnit":
        return self._compilation_unit

    # region Signature
    ###################################################################################
    ###################################################################################

    @staticmethod
    def _convert_type_for_solidity_signature(t: Optional[Union[Type, List[Type]]]):
        # pylint: disable=import-outside-toplevel
        from slither.core.declarations import Contract

        if isinstance(t, UserDefinedType) and isinstance(t.type, Contract):
            return "address"
        return str(t)

    @property
    def solidity_signature(self) -> str:
        """
        Return a signature following the Solidity Standard
        Contract and converted into address
        :return: the solidity signature
        """
        if self._solidity_signature is None:
            parameters = [
                self._convert_type_for_solidity_signature(x.type) for x in self.parameters
            ]
            self._solidity_signature = self.name + "(" + ",".join(parameters) + ")"
        return self._solidity_signature

    # endregion
    ###################################################################################
    ###################################################################################

    def __str__(self):
        return "revert " + self.solidity_signature
