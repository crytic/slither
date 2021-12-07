from typing import List, Any, Dict, Optional, Union
from crytic_compile.utils.naming import Filename

from slither.core.declarations import Contract, Import, Pragma
from slither.core.declarations.custom_error_top_level import CustomErrorTopLevel
from slither.core.declarations.enum_top_level import EnumTopLevel
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.core.declarations.structure_top_level import StructureTopLevel
from slither.slithir.variables import Constant

#pylint: disable=too-many-instance-attributes
class FileScope:
    def __init__(self, filename: Filename):
        self.filename = filename
        self.accessible_scopes: List[FileScope] = []

        self.contracts: Dict[str, Contract] = dict()
        # Custom error are a list instead of a dict
        # Because we parse the function signature later on
        # So we simplify the logic and have the scope fields all populated
        self.custom_errors: List[CustomErrorTopLevel] = []
        self.enums: Dict[str, EnumTopLevel] = dict()
        # Functions is a list instead of a dict
        # Because we parse the function signature later on
        # So we simplify the logic and have the scope fields all populated
        self.functions: List[FunctionTopLevel] = []
        self.imports: List[Import] = []
        self.pragmas: List[Pragma] = []
        self.structures: Dict[str, StructureTopLevel] = dict()

        self.accessible_scope_done = False

    def add_accesible_scopes(self) -> bool:
        if self.accessible_scope_done:
            return True

        if not self.accessible_scopes:
            self.accessible_scope_done = True
            return True

        if any(not new_scope.accessible_scope_done for new_scope in self.accessible_scopes):
            return False

        for new_scope in self.accessible_scopes:
            self.contracts.update(new_scope.contracts)
            self.custom_errors += new_scope.custom_errors
            self.enums.update(new_scope.enums)
            self.functions += new_scope.functions
            self.imports += new_scope.imports
            self.pragmas += new_scope.pragmas
            self.structures.update(new_scope.structures)

        self.accessible_scope_done = True
        return True

    def get_contract_from_name(self, name: Union[str, Constant]) -> Optional[Contract]:
        if isinstance(name, Constant):
            return self.contracts.get(name.name, None)
        return self.contracts.get(name, None)

    # region Built in definitions
    ###################################################################################
    ###################################################################################

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return other == self.filename
        return NotImplemented

    def __neq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return other != self.filename
        return NotImplemented

    def __str__(self) -> str:
        return str(self.filename.relative)

    def __hash__(self) -> int:
        return hash(self.filename.relative)

    # endregion
