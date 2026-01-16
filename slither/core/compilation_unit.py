import math
from enum import Enum
from typing import TYPE_CHECKING

from crytic_compile import CompilationUnit, CryticCompile
from crytic_compile.compiler.compiler import CompilerVersion
from crytic_compile.utils.naming import Filename

from slither.core.context.context import Context
from slither.core.declarations import (
    Contract,
    Pragma,
    Import,
    Function,
    Modifier,
)
from slither.core.declarations.custom_error_top_level import CustomErrorTopLevel
from slither.core.declarations.enum_top_level import EnumTopLevel
from slither.core.declarations.event_top_level import EventTopLevel
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.core.declarations.structure_top_level import StructureTopLevel
from slither.core.declarations.using_for_top_level import UsingForTopLevel
from slither.core.scope.scope import FileScope
from slither.core.solidity_types.type_alias import TypeAliasTopLevel
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.top_level_variable import TopLevelVariable
from slither.slithir.operations import InternalCall
from slither.slithir.variables import Constant

if TYPE_CHECKING:
    from slither.core.slither_core import SlitherCore


class Language(Enum):
    SOLIDITY = "solidity"
    VYPER = "vyper"

    @staticmethod
    def from_str(label: str):
        if label == "solc":
            return Language.SOLIDITY
        if label == "vyper":
            return Language.VYPER

        raise ValueError(f"Unknown language: {label}")


class SlitherCompilationUnit(Context):
    def __init__(self, core: "SlitherCore", crytic_compilation_unit: CompilationUnit) -> None:
        super().__init__()

        self._core = core
        self._crytic_compile_compilation_unit = crytic_compilation_unit
        self._language = Language.from_str(crytic_compilation_unit.compiler_version.compiler)

        # Top level object
        self.contracts: list[Contract] = []
        self._structures_top_level: list[StructureTopLevel] = []
        self._enums_top_level: list[EnumTopLevel] = []
        self._events_top_level: list[EventTopLevel] = []
        self._variables_top_level: list[TopLevelVariable] = []
        self._functions_top_level: list[FunctionTopLevel] = []
        self._using_for_top_level: list[UsingForTopLevel] = []
        self._pragma_directives: list[Pragma] = []
        self._import_directives: list[Import] = []
        self._custom_errors: list[CustomErrorTopLevel] = []
        self._type_aliases: dict[str, TypeAliasTopLevel] = {}

        self._all_functions: set[Function] = set()
        self._all_modifiers: set[Modifier] = set()

        # Memoize
        self._all_state_variables: set[StateVariable] | None = None

        self._persistent_storage_layouts: dict[str, dict[str, tuple[int, int]]] = {}
        self._transient_storage_layouts: dict[str, dict[str, tuple[int, int]]] = {}

        self._contract_with_missing_inheritance: set[Contract] = set()

        self._source_units: dict[int, str] = {}

        self.counter_slithir_tuple = 0
        self.counter_slithir_temporary = 0
        self.counter_slithir_reference = 0

        self.scopes: dict[Filename, FileScope] = {}

    @property
    def core(self) -> "SlitherCore":
        return self._core

    @property
    def source_units(self) -> dict[int, str]:
        return self._source_units

    # endregion
    ###################################################################################
    ###################################################################################
    # region Compiler
    ###################################################################################
    ###################################################################################
    @property
    def language(self) -> Language:
        return self._language

    @property
    def is_vyper(self) -> bool:
        return self._language == Language.VYPER

    @property
    def is_solidity(self) -> bool:
        return self._language == Language.SOLIDITY

    @property
    def compiler_version(self) -> CompilerVersion:
        return self._crytic_compile_compilation_unit.compiler_version

    @property
    def solc_version(self) -> str:
        # TODO: make version a non optional argument of compiler version in cc
        return self._crytic_compile_compilation_unit.compiler_version.version  # type:ignore

    @property
    def crytic_compile_compilation_unit(self) -> CompilationUnit:
        return self._crytic_compile_compilation_unit

    @property
    def crytic_compile(self) -> CryticCompile:
        return self._crytic_compile_compilation_unit.crytic_compile

    # endregion
    ###################################################################################
    ###################################################################################
    # region Pragma attributes
    ###################################################################################
    ###################################################################################

    @property
    def pragma_directives(self) -> list[Pragma]:
        """list(core.declarations.Pragma): Pragma directives."""
        return self._pragma_directives

    @property
    def import_directives(self) -> list[Import]:
        """list(core.declarations.Import): Import directives"""
        return self._import_directives

    # endregion
    ###################################################################################
    ###################################################################################
    # region Contracts
    ###################################################################################
    ###################################################################################

    @property
    def contracts_derived(self) -> list[Contract]:
        """list(Contract): List of contracts that are derived and not inherited."""
        inheritances = [x.inheritance for x in self.contracts]
        inheritance = [item for sublist in inheritances for item in sublist]
        return [c for c in self.contracts if c not in inheritance]

    def get_contract_from_name(self, contract_name: str | Constant) -> list[Contract]:
        """
            Return a list of contract from a name
        Args:
            contract_name (str): name of the contract
        Returns:
            List[Contract]
        """
        return [c for c in self.contracts if c.name == contract_name]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Functions and modifiers
    ###################################################################################
    ###################################################################################

    @property
    def functions(self) -> list[Function]:
        return list(self._all_functions)

    def add_function(self, func: Function) -> None:
        self._all_functions.add(func)

    @property
    def modifiers(self) -> list[Modifier]:
        return list(self._all_modifiers)

    def add_modifier(self, modif: Modifier) -> None:
        self._all_modifiers.add(modif)

    @property
    def functions_and_modifiers(self) -> list[Function]:
        return self.functions + list(self.modifiers)

    def propagate_function_calls(self) -> None:
        """This info is used to compute the rvalues of Phi operations in `fix_phi` and ultimately
        is responsible for the `read` property of Phi operations which is vital to
        propagating taints inter-procedurally
        """
        for f in self.functions_and_modifiers:
            for node in f.nodes:
                for ir in node.irs_ssa:
                    if isinstance(ir, InternalCall):
                        assert ir.function
                        ir.function.add_reachable_from_node(node, ir)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Variables
    ###################################################################################
    ###################################################################################

    @property
    def state_variables(self) -> list[StateVariable]:
        if self._all_state_variables is None:
            state_variabless = [c.state_variables for c in self.contracts]
            state_variables = [item for sublist in state_variabless for item in sublist]
            self._all_state_variables = set(state_variables)
        return list(self._all_state_variables)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Top level
    ###################################################################################
    ###################################################################################

    @property
    def structures_top_level(self) -> list[StructureTopLevel]:
        return self._structures_top_level

    @property
    def enums_top_level(self) -> list[EnumTopLevel]:
        return self._enums_top_level

    @property
    def events_top_level(self) -> list[EventTopLevel]:
        return self._events_top_level

    @property
    def variables_top_level(self) -> list[TopLevelVariable]:
        return self._variables_top_level

    @property
    def functions_top_level(self) -> list[FunctionTopLevel]:
        return self._functions_top_level

    @property
    def using_for_top_level(self) -> list[UsingForTopLevel]:
        return self._using_for_top_level

    @property
    def custom_errors(self) -> list[CustomErrorTopLevel]:
        return self._custom_errors

    @property
    def type_aliases(self) -> dict[str, TypeAliasTopLevel]:
        return self._type_aliases

    # endregion
    ###################################################################################
    ###################################################################################
    # region Internals
    ###################################################################################
    ###################################################################################

    @property
    def contracts_with_missing_inheritance(self) -> set[Contract]:
        return self._contract_with_missing_inheritance

    # endregion
    ###################################################################################
    ###################################################################################
    # region Scope
    ###################################################################################
    ###################################################################################

    def get_scope(self, filename_str: str) -> FileScope:
        filename = self._crytic_compile_compilation_unit.crytic_compile.filename_lookup(
            filename_str
        )

        if filename not in self.scopes:
            self.scopes[filename] = FileScope(filename)

        return self.scopes[filename]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Storage Layouts
    ###################################################################################
    ###################################################################################

    def compute_storage_layout(self) -> None:
        assert self.is_solidity

        for contract in self.contracts_derived:
            self._compute_storage_layout(
                contract.name,
                contract.storage_variables_ordered,
                False,
                contract.custom_storage_layout,
            )
            self._compute_storage_layout(
                contract.name, contract.transient_variables_ordered, True, None
            )

    def _compute_storage_layout(
        self,
        contract_name: str,
        state_variables_ordered: list[StateVariable],
        is_transient: bool,
        custom_storage_layout: int | None,
    ):
        if is_transient:
            slot = 0
            self._transient_storage_layouts[contract_name] = {}
        else:
            slot = custom_storage_layout if custom_storage_layout else 0
            self._persistent_storage_layouts[contract_name] = {}

        offset = 0
        for var in state_variables_ordered:
            assert var.type
            size, new_slot = var.type.storage_size

            if new_slot:
                if offset > 0:
                    slot += 1
                    offset = 0
            elif size + offset > 32:
                slot += 1
                offset = 0

            if is_transient:
                self._transient_storage_layouts[contract_name][var.canonical_name] = (
                    slot,
                    offset,
                )
            else:
                self._persistent_storage_layouts[contract_name][var.canonical_name] = (
                    slot,
                    offset,
                )

            if new_slot:
                slot += math.ceil(size / 32)
            else:
                offset += size

    def storage_layout_of(self, contract: Contract, var: StateVariable) -> tuple[int, int]:
        if var.is_stored:
            return self._persistent_storage_layouts[contract.name][var.canonical_name]
        return self._transient_storage_layouts[contract.name][var.canonical_name]

    # endregion
