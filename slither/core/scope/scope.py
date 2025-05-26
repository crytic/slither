from typing import List, Any, Dict, Optional, Union, Set, TypeVar, Callable

from crytic_compile import CompilationUnit
from crytic_compile.source_unit import SourceUnit
from crytic_compile.utils.naming import Filename

from slither.core.declarations import Contract, Import, Pragma
from slither.core.declarations.custom_error_top_level import CustomErrorTopLevel
from slither.core.declarations.enum_top_level import EnumTopLevel
from slither.core.declarations.event_top_level import EventTopLevel
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


# pylint: disable=too-many-instance-attributes
class FileScope:
    def __init__(self, filename: Filename) -> None:
        self.filename = filename
        self.accessible_scopes: List[FileScope] = []
        self.exported_symbols: Set[int] = set()

        self.contracts: Dict[str, Contract] = {}
        # Custom error are a list instead of a dict
        # Because we parse the function signature later on
        # So we simplify the logic and have the scope fields all populated
        self.custom_errors: Set[CustomErrorTopLevel] = set()
        self.enums: Dict[str, EnumTopLevel] = {}
        # Functions is a list instead of a dict
        # Because we parse the function signature later on
        # So we simplify the logic and have the scope fields all populated
        self.functions: Set[FunctionTopLevel] = set()
        self.events: Set[EventTopLevel] = set()
        self.using_for_directives: Set[UsingForTopLevel] = set()
        self.imports: Set[Import] = set()
        self.pragmas: Set[Pragma] = set()
        self.structures: Dict[str, StructureTopLevel] = {}
        self.variables: Dict[str, TopLevelVariable] = {}

        # Renamed created by import
        # import A as B
        # local name -> original name (A -> B)
        self.renaming: Dict[str, str] = {}

        # User defined types
        # Name -> type alias
        self.type_aliases: Dict[str, TypeAlias] = {}

    def add_accessible_scopes(self) -> bool:  # pylint: disable=too-many-branches
        """
        Add information from accessible scopes. Return true if new information was obtained
        :return:
        :rtype:
        """

        learn_something = False
        for new_scope in self.accessible_scopes:
            # To support using for directives on user defined types and user defined functions,
            # we need to propagate the using for directives from the imported file to the importing file
            # since it is not reflected in the "exportedSymbols" field of the AST.
            if not new_scope.using_for_directives.issubset(self.using_for_directives):
                self.using_for_directives |= new_scope.using_for_directives
                learn_something = True
            if not _dict_contain(new_scope.type_aliases, self.type_aliases):
                self.type_aliases.update(new_scope.type_aliases)
                learn_something = True
            if not new_scope.functions.issubset(self.functions):
                self.functions |= new_scope.functions
                learn_something = True

            # To get around this bug for aliases https://github.com/ethereum/solidity/pull/11881,
            # we propagate the exported_symbols from the imported file to the importing file
            # See tests/e2e/solc_parsing/test_data/top-level-nested-import-0.7.1.sol
            if not new_scope.exported_symbols.issubset(self.exported_symbols):
                self.exported_symbols |= new_scope.exported_symbols
                learn_something = True

            # This is need to support aliasing when we do a late lookup using SolidityImportPlaceholder
            if not _dict_contain(new_scope.renaming, self.renaming):
                self.renaming.update(new_scope.renaming)
                learn_something = True

        return learn_something

    def get_contract_from_name(self, name: Union[str, Constant]) -> Optional[Contract]:
        if isinstance(name, Constant):
            return self.contracts.get(name.name, None)
        return self.contracts.get(name, None)

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
