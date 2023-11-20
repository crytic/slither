from typing import List, Any, Dict, Optional, Union, Set, TypeVar, Callable, Tuple

from crytic_compile import CompilationUnit
from crytic_compile.source_unit import SourceUnit
from crytic_compile.utils.naming import Filename

from slither.core.declarations import Contract, Import, Pragma
from slither.core.declarations.custom_error_top_level import CustomErrorTopLevel
from slither.core.declarations.enum_top_level import EnumTopLevel
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.core.declarations.using_for_top_level import UsingForTopLevel
from slither.core.declarations.structure_top_level import StructureTopLevel
from slither.core.solidity_types import TypeAlias
from slither.core.variables.top_level_variable import TopLevelVariable
from slither.slithir.variables import Constant


def _dict_contain(d1: Dict, d2: Dict) -> bool:
    """
    Return true if d1 is included in d2
    """
    d2_keys = d2.keys()
    return all(item in d2_keys for item in d1.keys())


def _dict_containn(d1: Dict, d2: Dict) -> bool:
    """
    Return true if d1 is included in d2
    """
    for sc, v in d1.items():
        if sc not in d2:
            return False
        d2_k = d2[sc].keys()
        if not all(item in d2_k for item in v.keys()):
            return False
    return True


# pylint: disable=too-many-instance-attributes
class FileScope:
    def __init__(self, filename: Filename) -> None:
        self.filename = filename
        self.accessible_scopes: List[FileScopeToImport] = []
        # Dict[str, Dict[str, Contract]] --- Filename/Scope -> Name -> Contract
        # quelli renaming avranno il corretto filename dove trovare l item corretto
        # gli altri è univoco per forza tra i filename (edge case uno rinominato l altro no non univoco)
        # dopo add_accesible_scopes applichi il renaming direttamente cosi original name diventa local name
        # poi non ci pensi piu e.g. in find variable ecc
        self.contracts: Dict[str, Dict[str, Contract]] = {}
        self.custom_errors: Dict[str, Dict[str, CustomErrorTopLevel]] = {}
        self.enums: Dict[str, Dict[str, EnumTopLevel]] = {}
        self.functions: Dict[str, Dict[str, FunctionTopLevel]] = {}
        self.using_for_directives: Set[UsingForTopLevel] = set()
        self.imports: Set[Import] = set()
        self.pragmas: Set[Pragma] = set()
        self.structures: Dict[str, Dict[str, StructureTopLevel]] = {}
        self.variables: Dict[str, Dict[str, TopLevelVariable]] = {}

        # Renamed created by import
        # import A as B
        # local name -> original name (A -> B)
        # local name -> (original name, filename) (A -> (B, I.sol))
        self.renaming: Dict[str, Tuple[str, str]] = {}

        # User defined types
        # Name -> type alias
        self.type_aliases: Dict[str, Dict[str, TypeAlias]] = {}

    def add_accesible_scopes(self) -> bool:
        """
        Add information from accessible scopes. Return true if new information was obtained

        :return:
        :rtype:
        """

        learn_something = False

        for new_scope in self.accessible_scopes:
            if not _dict_containn(new_scope.contracts, self.contracts):
                #print(f"before {self.contracts}")
                self.contracts.update(new_scope.contracts)
                #print(f"after {self.contracts}")
                learn_something = True
            #if not new_scope.custom_errors.issubset(self.custom_errors):
            #    self.custom_errors |= new_scope.custom_errors
            #    learn_something = True
            if not _dict_containn(new_scope.custom_errors, self.custom_errors):
                self.custom_errors.update(new_scope.custom_errors)
                learn_something = True
            if not _dict_containn(new_scope.enums, self.enums):
                self.enums.update(new_scope.enums)
                learn_something = True
            if not _dict_containn(new_scope.functions, self.functions):
                self.functions.update(new_scope.functions)
                learn_something = True
            #if not new_scope.functions.issubset(self.functions):
            #    self.functions |= new_scope.functions
            #    learn_something = True
            if not new_scope.using_for_directives.issubset(self.using_for_directives):
                self.using_for_directives |= new_scope.using_for_directives
                learn_something = True
            if not new_scope.imports.issubset(self.imports):
                self.imports |= new_scope.imports
                learn_something = True
            if not new_scope.pragmas.issubset(self.pragmas):
                self.pragmas |= new_scope.pragmas
                learn_something = True
            if not _dict_containn(new_scope.structures, self.structures):
                #print(f"before {self.contracts}")
                self.structures.update(new_scope.structures)
                #print(f"after {self.contracts}")
                learn_something = True
            if not _dict_containn(new_scope.variables, self.variables):
                self.variables.update(new_scope.variables)
                learn_something = True
            if not _dict_contain(new_scope.renaming, self.renaming):
                self.renaming.update(new_scope.renaming)
                learn_something = True
            if not _dict_containn(new_scope.type_aliases, self.type_aliases):
                self.type_aliases.update(new_scope.type_aliases)
                learn_something = True

        return learn_something

    def get_contract_from_name(self, name: Union[str, Constant]) -> Optional[Contract]:
        if isinstance(name, Constant):
            for s in self.contracts.values():
                if name.name in s:
                    return s[name.name]
            return None
        for s in self.contracts.values():
            if name in s:
                return s[name]
        return None

    AbstractReturnType = TypeVar("AbstractReturnType")

    def _generic_source_unit_getter(
        self,
        crytic_compile_compilation_unit: CompilationUnit,
        name: str,
        getter: Callable[[SourceUnit], Dict[str, AbstractReturnType]],
    ) -> Optional[AbstractReturnType]:

        assert self.filename in crytic_compile_compilation_unit.source_units

        source_unit = crytic_compile_compilation_unit.source_unit(self.filename)

        if name in getter(source_unit):
            return getter(source_unit)[name]

        for scope in self.accessible_scopes:
            source_unit = crytic_compile_compilation_unit.source_unit(scope.filename)
            if name in getter(source_unit):
                return getter(source_unit)[name]

        return None

    def bytecode_init(
        self, crytic_compile_compilation_unit: CompilationUnit, contract_name: str
    ) -> Optional[str]:
        """
        Return the init bytecode

        Args:
            crytic_compile_compilation_unit:
            contract_name:

        Returns:

        """
        getter: Callable[[SourceUnit], Dict[str, str]] = lambda x: x.bytecodes_init
        return self._generic_source_unit_getter(
            crytic_compile_compilation_unit, contract_name, getter
        )

    def bytecode_runtime(
        self, crytic_compile_compilation_unit: CompilationUnit, contract_name: str
    ) -> Optional[str]:
        """
        Return the runtime bytecode

        Args:
            crytic_compile_compilation_unit:
            contract_name:

        Returns:

        """
        getter: Callable[[SourceUnit], Dict[str, str]] = lambda x: x.bytecodes_runtime
        return self._generic_source_unit_getter(
            crytic_compile_compilation_unit, contract_name, getter
        )

    def srcmap_init(
        self, crytic_compile_compilation_unit: CompilationUnit, contract_name: str
    ) -> Optional[List[str]]:
        """
        Return the init scrmap

        Args:
            crytic_compile_compilation_unit:
            contract_name:

        Returns:

        """
        getter: Callable[[SourceUnit], Dict[str, List[str]]] = lambda x: x.srcmaps_init
        return self._generic_source_unit_getter(
            crytic_compile_compilation_unit, contract_name, getter
        )

    def srcmap_runtime(
        self, crytic_compile_compilation_unit: CompilationUnit, contract_name: str
    ) -> Optional[List[str]]:
        """
        Return the runtime srcmap

        Args:
            crytic_compile_compilation_unit:
            contract_name:

        Returns:

        """
        getter: Callable[[SourceUnit], Dict[str, List[str]]] = lambda x: x.srcmaps_runtime
        return self._generic_source_unit_getter(
            crytic_compile_compilation_unit, contract_name, getter
        )

    def abi(self, crytic_compile_compilation_unit: CompilationUnit, contract_name: str) -> Any:
        """
        Return the abi

        Args:
            crytic_compile_compilation_unit:
            contract_name:

        Returns:

        """
        getter: Callable[[SourceUnit], Dict[str, List[str]]] = lambda x: x.abis
        return self._generic_source_unit_getter(
            crytic_compile_compilation_unit, contract_name, getter
        )

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

class FileScopeToImport:
    def __init__(self, filescope: FileScope, items_to_import: List[str]) -> None:
        self.filescope = filescope
        self.items_to_import = items_to_import
    
    @property
    def contracts(self) -> Dict[str, Dict[str, Contract]]:
        if len(self.items_to_import) != 0:
            result = {}
            for scope, elems in self.filescope.contracts.items():
                for elem in elems:
                    if elem in self.items_to_import:
                        if not scope in result:
                            result[scope] = {}
                        result[scope][elem] = elems[elem]
            return result
        return self.filescope.contracts
    """
    @property
    def custom_errors(self) -> Set[CustomErrorTopLevel]:
        if len(self.items_to_import) != 0:
            result = set()
            for custom_error in self.filescope.custom_errors:
                if custom_error.name in self.items_to_import:
                    result.add(custom_error)
            return result
        return self.filescope.custom_errors
    """
    @property
    def custom_errors(self) -> Dict[str, Dict[str, CustomErrorTopLevel]]:
        if len(self.items_to_import) != 0:
            result = {}
            for scope, elems in self.filescope.custom_errors.items():
                for elem in elems:
                    if elem in self.items_to_import:
                        if not scope in result:
                            result[scope] = {}
                        result[scope][elem] = elems[elem]
            return result
        return self.filescope.custom_errors

    """
    @property
    def enums(self) -> Dict[str, EnumTopLevel]:
        if len(self.items_to_import) != 0:
            result = {}
            for name, enum in self.filescope.enums.items():
                if name in self.items_to_import:
                    result[name] = enum
            return result
        return self.filescope.enums
    """

    @property
    def enums(self) -> Dict[str, Dict[str, EnumTopLevel]]:
        if len(self.items_to_import) != 0:
            result = {}
            for scope, elems in self.filescope.enums.items():
                for elem in elems:
                    if elem in self.items_to_import:
                        if not scope in result:
                            result[scope] = {}
                        result[scope][elem] = elems[elem]
            return result
        return self.filescope.enums
    """
    @property
    def functions(self) -> Set[FunctionTopLevel]:
        if len(self.items_to_import) != 0:
            result = set()
            for function in self.filescope.functions:
                if function.name in self.items_to_import:
                    result.add(function)
            return result
        return self.filescope.functions
    """

    @property
    def functions(self) -> Dict[str, Dict[str, FunctionTopLevel]]:
        if len(self.items_to_import) != 0:
            result = {}
            for scope, elems in self.filescope.functions.items():
                for elem in elems:
                    if elem in self.items_to_import:
                        if not scope in result:
                            result[scope] = {}
                        result[scope][elem] = elems[elem]
            return result
        return self.filescope.functions


    @property
    def using_for_directives(self) -> Set[UsingForTopLevel]:
        # TODO check it's correct
        if len(self.items_to_import) == 0:
            return self.filescope.using_for_directives
        return set()
        
    @property
    def imports(self) -> Set[Import]:
        # TODO check it's correct
        if len(self.items_to_import) == 0:
            return self.filescope.imports
        return set()

    @property
    def pragmas(self) -> Set[Pragma]:
        # TODO check it's correct
        return self.filescope.pragmas

    """
    @property
    def structures(self) -> Dict[str, StructureTopLevel]:
        if len(self.items_to_import) != 0:
            result = {}
            for name, structure in self.filescope.structures.items():
                if name in self.items_to_import:
                    result[name] = structure
            return result
        return self.filescope.structures
    """
    @property
    def structures(self) -> Dict[str, Dict[str, StructureTopLevel]]:
        if len(self.items_to_import) != 0:
            result = {}
            for scope, elems in self.filescope.structures.items():
                for elem in elems:
                    if elem in self.items_to_import:
                        if not scope in result:
                            result[scope] = {}
                        result[scope][elem] = elems[elem]
            return result
        return self.filescope.structures
    """
    @property
    def variables(self) -> Dict[str, TopLevelVariable]:
        if len(self.items_to_import) != 0:
            result = {}
            for name, variable in self.filescope.variables.items():
                if name in self.items_to_import:
                    result[name] = variable
            return result
        return self.filescope.variables
    """
    @property
    def variables(self) -> Dict[str, Dict[str, TopLevelVariable]]:
        if len(self.items_to_import) != 0:
            result = {}
            for scope, elems in self.filescope.variables.items():
                for elem in elems:
                    if elem in self.items_to_import:
                        if not scope in result:
                            result[scope] = {}
                        result[scope][elem] = elems[elem]
            return result
        return self.filescope.variables


    @property
    def renaming(self) -> Dict[str, str]:
        # TODO check it's correct
        return self.filescope.renaming

    """
    @property
    def type_aliases(self) -> Dict[str, Dict[str, TypeAlias]]:
        # TODO check it's correct
        return self.filescope.type_aliases
    """

    @property
    def type_aliases(self) -> Dict[str, Dict[str, TypeAlias]]:
        if len(self.items_to_import) != 0:
            result = {}
            for scope, elems in self.filescope.type_aliases.items():
                for elem in elems:
                    if elem in self.items_to_import:
                        if not scope in result:
                            result[scope] = {}
                        result[scope][elem] = elems[elem]
            return result
        return self.filescope.type_aliases
