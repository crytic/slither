from typing import List, Any, Dict, Optional, Union, Set
from crytic_compile.utils.naming import Filename

from slither.core.declarations import Contract, Import, Pragma
from slither.core.declarations.custom_error_top_level import CustomErrorTopLevel
from slither.core.declarations.enum_top_level import EnumTopLevel
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.core.declarations.structure_top_level import StructureTopLevel
from slither.slithir.variables import Constant


def _dict_contain(d1: Dict, d2: Dict) -> bool:
    """
    Return true if d1 is included in d2
    """
    d2_keys = d2.keys()
    return all(item in d2_keys for item in d1.keys())


# pylint: disable=too-many-instance-attributes
class FileScope:
    def __init__(self, filename: Filename):
        self.filename = filename
        self.accessible_scopes: List[FileScope] = []

        self.contracts: Dict[str, Contract] = dict()
        # Custom error are a list instead of a dict
        # Because we parse the function signature later on
        # So we simplify the logic and have the scope fields all populated
        self.custom_errors: Set[CustomErrorTopLevel] = set()
        self.enums: Dict[str, EnumTopLevel] = dict()
        # Functions is a list instead of a dict
        # Because we parse the function signature later on
        # So we simplify the logic and have the scope fields all populated
        self.functions: Set[FunctionTopLevel] = set()
        self.imports: Set[Import] = set()
        self.pragmas: Set[Pragma] = set()
        self.structures: Dict[str, StructureTopLevel] = dict()

    def add_accesible_scopes(self) -> bool:
        """
        Add information from accessible scopes. Return true if new information was obtained

        :return:
        :rtype:
        """

        learn_something = False

        for new_scope in self.accessible_scopes:
            if not _dict_contain(new_scope.contracts, self.contracts):
                self.contracts.update(new_scope.contracts)
                learn_something = True
            if not new_scope.custom_errors.issubset(self.custom_errors):
                self.custom_errors |= new_scope.custom_errors
                learn_something = True
            if not _dict_contain(new_scope.enums, self.enums):
                self.enums.update(new_scope.enums)
                learn_something = True
            if not new_scope.functions.issubset(self.functions):
                self.functions |= new_scope.functions
                learn_something = True
            if not new_scope.imports.issubset(self.imports):
                self.imports |= new_scope.imports
                learn_something = True
            if not new_scope.pragmas.issubset(self.pragmas):
                self.pragmas |= new_scope.pragmas
                learn_something = True
            if not _dict_contain(new_scope.structures, self.structures):
                self.structures.update(new_scope.structures)
                learn_something = True

        return learn_something

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
