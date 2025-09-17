""""
    Contract module
"""
import logging
from collections import defaultdict
from pathlib import Path
from typing import Optional, List, Dict, Callable, Tuple, TYPE_CHECKING, Union, Set, Any

from crytic_compile.platform import Type as PlatformType

from slither.core.cfg.scope import Scope
from slither.core.solidity_types.type import Type
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.utils.using_for import USING_FOR, merge_using_for
from slither.core.declarations.function import Function, FunctionType, FunctionLanguage
from slither.utils.erc import (
    ERC20_signatures,
    ERC165_signatures,
    ERC223_signatures,
    ERC721_signatures,
    ERC1820_signatures,
    ERC777_signatures,
    ERC1155_signatures,
    ERC1967_signatures,
    ERC2612_signatures,
    ERC1363_signatures,
    ERC4524_signatures,
    ERC4626_signatures,
)
from slither.utils.tests_pattern import is_test_contract

# pylint: disable=too-many-lines,too-many-instance-attributes,import-outside-toplevel,too-many-nested-blocks
if TYPE_CHECKING:
    from slither.core.declarations import (
        Enum,
        EventContract,
        Modifier,
        EnumContract,
        StructureContract,
        FunctionContract,
        CustomErrorContract,
    )
    from slither.slithir.operations import HighLevelCall, LibraryCall
    from slither.slithir.variables.variable import SlithIRVariable
    from slither.core.variables import Variable, StateVariable
    from slither.core.compilation_unit import SlitherCompilationUnit
    from slither.core.scope.scope import FileScope
    from slither.core.cfg.node import Node
    from slither.core.solidity_types import TypeAliasContract


LOGGER = logging.getLogger("Contract")


class Contract(SourceMapping):  # pylint: disable=too-many-public-methods
    """
    Contract class
    """

    def __init__(self, compilation_unit: "SlitherCompilationUnit", scope: "FileScope") -> None:
        super().__init__()

        self._name: Optional[str] = None
        self._id: Optional[int] = None
        self._inheritance: List["Contract"] = []  # all contract inherited, c3 linearization
        self._immediate_inheritance: List["Contract"] = []  # immediate inheritance

        # Constructors called on contract's definition
        # contract B is A(1) { ..
        self._explicit_base_constructor_calls: List["Contract"] = []

        self._enums: Dict[str, "EnumContract"] = {}
        self._structures: Dict[str, "StructureContract"] = {}
        self._events: Dict[str, "EventContract"] = {}
        # map accessible variable from name -> variable
        # do not contain private variables inherited from contract
        self._variables: Dict[str, "StateVariable"] = {}
        self._variables_ordered: List["StateVariable"] = []
        # Reference id -> variable declaration (only available for compact AST)
        self._state_variables_by_ref_id: Dict[int, "StateVariable"] = {}
        self._modifiers: Dict[str, "Modifier"] = {}
        self._functions: Dict[str, "FunctionContract"] = {}
        self._linearizedBaseContracts: List[int] = []
        self._custom_errors: Dict[str, "CustomErrorContract"] = {}
        self._type_aliases: Dict[str, "TypeAliasContract"] = {}

        # The only str is "*"
        self._using_for: USING_FOR = {}
        self._using_for_complete: Optional[USING_FOR] = None
        self._kind: Optional[str] = None
        self._is_interface: bool = False
        self._is_library: bool = False
        self._is_fully_implemented: bool = False
        self._is_abstract: bool = False

        self._signatures: Optional[List[str]] = None
        self._signatures_declared: Optional[List[str]] = None

        self._fallback_function: Optional["FunctionContract"] = None
        self._receive_function: Optional["FunctionContract"] = None

        self._is_upgradeable: Optional[bool] = None
        self._is_upgradeable_proxy: Optional[bool] = None
        self._is_upgradeable_proxy_confirmed: Optional[bool] = None
        self._is_proxy: Optional[bool] = None
        self._is_admin_only_proxy: Optional[bool] = None
        self._delegate_variable: Optional["Variable"] = None
        self._delegate_contract: Optional["Contract"] = None
        self._proxy_impl_setter: Optional["Function"] = None
        self._proxy_impl_getter: Optional["Function"] = None
        self._proxy_impl_slot: Optional["Variable"] = None
        self._uses_call_not_delegatecall: Optional[bool] = None

        self.is_top_level = False  # heavily used, so no @property
        self._upgradeable_version: Optional[str] = None

        self._initial_state_variables: List["StateVariable"] = []  # ssa

        self._is_incorrectly_parsed: bool = False

        self._available_functions_as_dict: Optional[Dict[str, "Function"]] = None
        self._all_functions_called: Optional[List["Function"]] = None

        self.compilation_unit: "SlitherCompilationUnit" = compilation_unit
        self.file_scope: "FileScope" = scope

        # memoize
        self._state_variables_used_in_reentrant_targets: Optional[
            Dict["StateVariable", Set[Union["StateVariable", "Function"]]]
        ] = None

        self._comments: Optional[str] = None

    ###################################################################################
    ###################################################################################
    # region General's properties
    ###################################################################################
    ###################################################################################

    @property
    def name(self) -> str:
        """str: Name of the contract."""
        assert self._name
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def id(self) -> int:
        """Unique id."""
        assert self._id is not None
        return self._id

    @id.setter
    def id(self, new_id: int) -> None:
        """Unique id."""
        self._id = new_id

    @property
    def contract_kind(self) -> Optional[str]:
        """
        contract_kind can be None if the legacy ast format is used
        :return:
        """
        return self._kind

    @contract_kind.setter
    def contract_kind(self, kind: str) -> None:
        self._kind = kind

    @property
    def is_interface(self) -> bool:
        return self._is_interface

    @is_interface.setter
    def is_interface(self, is_interface: bool) -> None:
        self._is_interface = is_interface

    @property
    def is_library(self) -> bool:
        return self._is_library

    @is_library.setter
    def is_library(self, is_library: bool) -> None:
        self._is_library = is_library

    @property
    def comments(self) -> Optional[str]:
        """
        Return the comments associated with the contract.

        When using comments, avoid strict text matching, as the solc behavior might change.
        For example, for old solc version, the first space after the * is not kept, i.e:

          * @title Test Contract
          * @dev Test comment

        Returns
        - " @title Test Contract\n @dev Test comment" for newest versions
        - "@title Test Contract\n@dev Test comment" for older versions


        Returns:
            the comment as a string
        """
        return self._comments

    @comments.setter
    def comments(self, comments: str):
        self._comments = comments

    @property
    def is_fully_implemented(self) -> bool:
        """
        bool: True if the contract defines all functions.
        In modern Solidity, virtual functions can lack an implementation.
        Prior to Solidity 0.6.0, functions like the following would be not fully implemented:
        ```solidity
        contract ImplicitAbstract{
            function f() public;
        }
        ```
        """
        return self._is_fully_implemented

    @is_fully_implemented.setter
    def is_fully_implemented(self, is_fully_implemented: bool):
        self._is_fully_implemented = is_fully_implemented

    @property
    def is_abstract(self) -> bool:
        """
        Note for Solidity < 0.6.0 it will always be false
        bool: True if the contract is abstract.
        """
        return self._is_abstract

    @is_abstract.setter
    def is_abstract(self, is_abstract: bool):
        self._is_abstract = is_abstract

    # endregion
    ###################################################################################
    ###################################################################################
    # region Structures
    ###################################################################################
    ###################################################################################

    @property
    def structures(self) -> List["StructureContract"]:
        """
        list(Structure): List of the structures
        """
        return list(self._structures.values())

    @property
    def structures_inherited(self) -> List["StructureContract"]:
        """
        list(Structure): List of the inherited structures
        """
        return [s for s in self.structures if s.contract != self]

    @property
    def structures_declared(self) -> List["StructureContract"]:
        """
        list(Structues): List of the structures declared within the contract (not inherited)
        """
        return [s for s in self.structures if s.contract == self]

    @property
    def structures_as_dict(self) -> Dict[str, "StructureContract"]:
        return self._structures

    # endregion
    ###################################################################################
    ###################################################################################
    # region Enums
    ###################################################################################
    ###################################################################################

    @property
    def enums(self) -> List["EnumContract"]:
        return list(self._enums.values())

    @property
    def enums_inherited(self) -> List["EnumContract"]:
        """
        list(Enum): List of the inherited enums
        """
        return [e for e in self.enums if e.contract != self]

    @property
    def enums_declared(self) -> List["EnumContract"]:
        """
        list(Enum): List of the enums declared within the contract (not inherited)
        """
        return [e for e in self.enums if e.contract == self]

    @property
    def enums_as_dict(self) -> Dict[str, "EnumContract"]:
        return self._enums

    # endregion
    ###################################################################################
    ###################################################################################
    # region Events
    ###################################################################################
    ###################################################################################

    @property
    def events(self) -> List["EventContract"]:
        """
        list(Event): List of the events
        """
        return list(self._events.values())

    @property
    def events_inherited(self) -> List["EventContract"]:
        """
        list(Event): List of the inherited events
        """
        return [e for e in self.events if e.contract != self]

    @property
    def events_declared(self) -> List["EventContract"]:
        """
        list(Event): List of the events declared within the contract (not inherited)
        """
        return [e for e in self.events if e.contract == self]

    @property
    def events_as_dict(self) -> Dict[str, "EventContract"]:
        return self._events

    # endregion
    ###################################################################################
    ###################################################################################
    # region Using for
    ###################################################################################
    ###################################################################################

    @property
    def using_for(self) -> USING_FOR:
        return self._using_for

    @property
    def using_for_complete(self) -> USING_FOR:
        """
        USING_FOR: Dict of merged local using for directive with top level directive
        """

        if self._using_for_complete is None:
            result = self.using_for
            top_level_using_for = self.file_scope.using_for_directives
            for uftl in top_level_using_for:
                result = merge_using_for(result, uftl.using_for)
            self._using_for_complete = result
        return self._using_for_complete

    # endregion
    ###################################################################################
    ###################################################################################
    # region Custom Errors
    ###################################################################################
    ###################################################################################

    @property
    def custom_errors(self) -> List["CustomErrorContract"]:
        """
        list(CustomErrorContract): List of the contract's custom errors
        """
        return list(self._custom_errors.values())

    @property
    def custom_errors_inherited(self) -> List["CustomErrorContract"]:
        """
        list(CustomErrorContract): List of the inherited custom errors
        """
        return [s for s in self.custom_errors if s.contract != self]

    @property
    def custom_errors_declared(self) -> List["CustomErrorContract"]:
        """
        list(CustomErrorContract): List of the custom errors declared within the contract (not inherited)
        """
        return [s for s in self.custom_errors if s.contract == self]

    @property
    def custom_errors_as_dict(self) -> Dict[str, "CustomErrorContract"]:
        return self._custom_errors

    # endregion
    ###################################################################################
    ###################################################################################
    # region Custom Errors
    ###################################################################################
    ###################################################################################

    @property
    def type_aliases(self) -> List["TypeAliasContract"]:
        """
        list(TypeAliasContract): List of the contract's custom errors
        """
        return list(self._type_aliases.values())

    @property
    def type_aliases_inherited(self) -> List["TypeAliasContract"]:
        """
        list(TypeAliasContract): List of the inherited custom errors
        """
        return [s for s in self.type_aliases if s.contract != self]

    @property
    def type_aliases_declared(self) -> List["TypeAliasContract"]:
        """
        list(TypeAliasContract): List of the custom errors declared within the contract (not inherited)
        """
        return [s for s in self.type_aliases if s.contract == self]

    @property
    def type_aliases_as_dict(self) -> Dict[str, "TypeAliasContract"]:
        return self._type_aliases

    # endregion
    ###################################################################################
    ###################################################################################
    # region Variables
    ###################################################################################
    ###################################################################################
    @property
    def state_variables_by_ref_id(self) -> Dict[int, "StateVariable"]:
        """
        Returns the state variables by reference id (only available for compact AST).
        """
        return self._state_variables_by_ref_id

    @property
    def variables(self) -> List["StateVariable"]:
        """
        Returns all the accessible variables (do not include private variable from inherited contract)

        list(StateVariable): List of the state variables. Alias to self.state_variables.
        """
        return list(self.state_variables)

    @property
    def variables_as_dict(self) -> Dict[str, "StateVariable"]:
        return self._variables

    @property
    def state_variables(self) -> List["StateVariable"]:
        """
        Returns all the accessible variables (do not include private variable from inherited contract).
        Use stored_state_variables_ordered for all the storage variables following the storage order
        Use transient_state_variables_ordered for all the transient variables following the storage order

        list(StateVariable): List of the state variables.
        """
        return list(self._variables.values())

    @property
    def state_variables_entry_points(self) -> List["StateVariable"]:
        """
        list(StateVariable): List of the state variables that are public.
        """
        return [var for var in self._variables.values() if var.visibility == "public"]

    @property
    def state_variables_ordered(self) -> List["StateVariable"]:
        """
        list(StateVariable): List of the state variables by order of declaration.
        """
        return self._variables_ordered

    def add_state_variables_ordered(self, new_vars: List["StateVariable"]) -> None:
        self._variables_ordered += new_vars

    @property
    def storage_variables_ordered(self) -> List["StateVariable"]:
        """
        list(StateVariable): List of the state variables in storage location by order of declaration.
        """
        return [v for v in self._variables_ordered if v.is_stored]

    @property
    def transient_variables_ordered(self) -> List["StateVariable"]:
        """
        list(StateVariable): List of the state variables in transient location by order of declaration.
        """
        return [v for v in self._variables_ordered if v.is_transient]

    @property
    def state_variables_inherited(self) -> List["StateVariable"]:
        """
        list(StateVariable): List of the inherited state variables
        """
        return [s for s in self.state_variables if s.contract != self]

    @property
    def state_variables_declared(self) -> List["StateVariable"]:
        """
        list(StateVariable): List of the state variables declared within the contract (not inherited)
        """
        return [s for s in self.state_variables if s.contract == self]

    @property
    def slithir_variables(self) -> List["SlithIRVariable"]:
        """
        List all of the slithir variables (non SSA)
        """
        slithir_variabless = [f.slithir_variables for f in self.functions + self.modifiers]  # type: ignore
        slithir_variables = [item for sublist in slithir_variabless for item in sublist]
        return list(set(slithir_variables))

    @property
    def state_variables_used_in_reentrant_targets(
        self,
    ) -> Dict["StateVariable", Set[Union["StateVariable", "Function"]]]:
        """
        Returns the state variables used in reentrant targets. Heuristics:
        - Variable used (read/write) in entry points that are reentrant
        - State variables that are public

        """
        from slither.core.variables.state_variable import StateVariable

        if self._state_variables_used_in_reentrant_targets is None:
            reentrant_functions = [f for f in self.functions_entry_points if f.is_reentrant]
            variables_used: Dict[
                StateVariable, Set[Union[StateVariable, "Function"]]
            ] = defaultdict(set)
            for function in reentrant_functions:
                for ir in function.all_slithir_operations():
                    state_variables = [v for v in ir.used if isinstance(v, StateVariable)]
                    for state_variable in state_variables:
                        variables_used[state_variable].add(ir.node.function)
            for variable in [v for v in self.state_variables if v.visibility == "public"]:
                variables_used[variable].add(variable)
            self._state_variables_used_in_reentrant_targets = variables_used
        return self._state_variables_used_in_reentrant_targets

    # endregion
    ###################################################################################
    ###################################################################################
    # region Constructors
    ###################################################################################
    ###################################################################################

    @property
    def constructor(self) -> Optional["Function"]:
        """
        Return the contract's immediate constructor.
        If there is no immediate constructor, returns the first constructor
        executed, following the c3 linearization
        Return None if there is no constructor.
        """
        cst = self.constructors_declared
        if cst:
            return cst
        for inherited_contract in self.inheritance:
            cst = inherited_contract.constructors_declared
            if cst:
                return cst
        return None

    @property
    def constructors_declared(self) -> Optional["Function"]:
        return next(
            (
                func
                for func in self.functions
                if func.is_constructor and func.contract_declarer == self
            ),
            None,
        )

    @property
    def constructors(self) -> List["FunctionContract"]:
        """
        Return the list of constructors (including inherited)
        """
        return [func for func in self.functions if func.is_constructor]

    @property
    def explicit_base_constructor_calls(self) -> List["Function"]:
        """
        list(Function): List of the base constructors called explicitly by this contract definition.

                        Base constructors called by any constructor definition will not be included.
                        Base constructors implicitly called by the contract definition (without
                        parenthesis) will not be included.

                        On "contract B is A(){..}" it returns the constructor of A
        """
        return [c.constructor for c in self._explicit_base_constructor_calls if c.constructor]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Functions and Modifiers
    ###################################################################################
    ###################################################################################

    @property
    def functions_signatures(self) -> List[str]:
        """
        Return the signatures of all the public/eterxnal functions/state variables
        :return: list(string) the signatures of all the functions that can be called
        """
        if self._signatures is None:
            sigs = [
                v.full_name for v in self.state_variables if v.visibility in ["public", "external"]
            ]

            sigs += {f.full_name for f in self.functions if f.visibility in ["public", "external"]}
            self._signatures = list(set(sigs))
        return self._signatures

    @property
    def functions_signatures_declared(self) -> List[str]:
        """
        Return the signatures of the public/eterxnal functions/state variables that are declared by this contract
        :return: list(string) the signatures of all the functions that can be called and are declared by this contract
        """
        if self._signatures_declared is None:
            sigs = [
                v.full_name
                for v in self.state_variables_declared
                if v.visibility in ["public", "external"]
            ]

            sigs += {
                f.full_name
                for f in self.functions_declared
                if f.visibility in ["public", "external"]
            }
            self._signatures_declared = list(set(sigs))
        return self._signatures_declared

    @property
    def functions(self) -> List["FunctionContract"]:
        """
        list(Function): List of the functions
        """
        return list(self._functions.values())

    def available_functions_as_dict(self) -> Dict[str, "Function"]:
        if self._available_functions_as_dict is None:
            self._available_functions_as_dict = {
                f.full_name: f for f in self._functions.values() if not f.is_shadowed
            }
        return self._available_functions_as_dict

    def add_function(self, func: "FunctionContract") -> None:
        self._functions[func.canonical_name] = func

    def set_functions(self, functions: Dict[str, "FunctionContract"]) -> None:
        """
        Set the functions

        :param functions:  dict full_name -> function
        :return:
        """
        self._functions = functions

    @property
    def functions_inherited(self) -> List["FunctionContract"]:
        """
        list(Function): List of the inherited functions
        """
        return [f for f in self.functions if f.contract_declarer != self]

    @property
    def functions_declared(self) -> List["FunctionContract"]:
        """
        list(Function): List of the functions defined within the contract (not inherited)
        """
        return [f for f in self.functions if f.contract_declarer == self]

    @property
    def functions_entry_points(self) -> List["FunctionContract"]:
        """
        list(Functions): List of public and external functions
        """
        return [
            f
            for f in self.functions
            if f.visibility in ["public", "external"] and not f.is_shadowed or f.is_fallback
        ]

    @property
    def modifiers(self) -> List["Modifier"]:
        """
        list(Modifier): List of the modifiers
        """
        return list(self._modifiers.values())

    def available_modifiers_as_dict(self) -> Dict[str, "Modifier"]:
        return {m.full_name: m for m in self._modifiers.values() if not m.is_shadowed}

    def set_modifiers(self, modifiers: Dict[str, "Modifier"]) -> None:
        """
        Set the modifiers

        :param modifiers:  dict full_name -> modifier
        :return:
        """
        self._modifiers = modifiers

    @property
    def modifiers_inherited(self) -> List["Modifier"]:
        """
        list(Modifier): List of the inherited modifiers
        """
        return [m for m in self.modifiers if m.contract_declarer != self]

    @property
    def modifiers_declared(self) -> List["Modifier"]:
        """
        list(Modifier): List of the modifiers defined within the contract (not inherited)
        """
        return [m for m in self.modifiers if m.contract_declarer == self]

    @property
    def functions_and_modifiers(self) -> List["Function"]:
        """
        list(Function|Modifier): List of the functions and modifiers
        """
        return self.functions + self.modifiers  # type: ignore

    @property
    def functions_and_modifiers_inherited(self) -> List["Function"]:
        """
        list(Function|Modifier): List of the inherited functions and modifiers
        """
        return self.functions_inherited + self.modifiers_inherited  # type: ignore

    @property
    def functions_and_modifiers_declared(self) -> List["Function"]:
        """
        list(Function|Modifier): List of the functions and modifiers defined within the contract (not inherited)
        """
        return self.functions_declared + self.modifiers_declared  # type: ignore

    @property
    def fallback_function(self) -> Optional["FunctionContract"]:
        if self._fallback_function is None:
            for f in self.functions:
                if f.is_fallback:
                    self._fallback_function = f
                    break
        return self._fallback_function

    @property
    def receive_function(self) -> Optional["FunctionContract"]:
        if self._receive_function is None:
            for f in self.functions:
                if f.is_receive:
                    self._receive_function = f
                    break
        return self._receive_function

    def available_elements_from_inheritances(
        self,
        elements: Dict[str, "Function"],
        getter_available: Callable[["Contract"], List["FunctionContract"]],
    ) -> Dict[str, "Function"]:
        """

        :param elements: dict(canonical_name -> elements)
        :param getter_available: fun x
        :return:
        """
        # keep track of the contracts visited
        # to prevent an ovveride due to multiple inheritance of the same contract
        # A is B, C, D is C, --> the second C was already seen
        inherited_elements: Dict[str, "FunctionContract"] = {}
        accessible_elements = {}
        contracts_visited = []
        for father in self.inheritance_reverse:
            functions: Dict[str, "FunctionContract"] = {
                v.full_name: v
                for v in getter_available(father)
                if v.contract not in contracts_visited
                and v.function_language
                != FunctionLanguage.Yul  # Yul functions are not propagated in the inheritance
            }
            contracts_visited.append(father)
            inherited_elements.update(functions)

        for element in inherited_elements.values():
            accessible_elements[element.full_name] = elements[element.canonical_name]

        return accessible_elements

    # endregion
    ###################################################################################
    ###################################################################################
    # region Inheritance
    ###################################################################################
    ###################################################################################

    @property
    def inheritance(self) -> List["Contract"]:
        """
        list(Contract): Inheritance list. Order: the first elem is the first father to be executed
        """
        return list(self._inheritance)

    @property
    def immediate_inheritance(self) -> List["Contract"]:
        """
        list(Contract): List of contracts immediately inherited from (fathers). Order: order of declaration.
        """
        return list(self._immediate_inheritance)

    @property
    def inheritance_reverse(self) -> List["Contract"]:
        """
        list(Contract): Inheritance list. Order: the last elem is the first father to be executed
        """
        return list(reversed(self._inheritance))

    def set_inheritance(
        self,
        inheritance: List["Contract"],
        immediate_inheritance: List["Contract"],
        called_base_constructor_contracts: List["Contract"],
    ) -> None:
        self._inheritance = inheritance
        self._immediate_inheritance = immediate_inheritance
        self._explicit_base_constructor_calls = called_base_constructor_contracts

    @property
    def derived_contracts(self) -> List["Contract"]:
        """
        list(Contract): Return the list of contracts derived from self
        """
        candidates = self.compilation_unit.contracts
        return [c for c in candidates if self in c.inheritance]  # type: ignore

    # endregion
    ###################################################################################
    ###################################################################################
    # region Getters from/to object
    ###################################################################################
    ###################################################################################

    def get_functions_reading_from_variable(self, variable: "Variable") -> List["Function"]:
        """
        Return the functions reading the variable
        """
        return [f for f in self.functions if f.is_reading(variable)]

    def get_functions_writing_to_variable(self, variable: "Variable") -> List["Function"]:
        """
        Return the functions writting the variable
        """
        return [f for f in self.functions if f.is_writing(variable)]

    def get_function_from_full_name(self, full_name: str) -> Optional["Function"]:
        """
            Return a function from a full name
            The full name differs from the solidity's signature are the type are conserved
            For example contract type are kept, structure are not unrolled, etc
        Args:
            full_name (str): signature of the function (without return statement)
        Returns:
            Function
        """
        return next(
            (f for f in self.functions if f.full_name == full_name and not f.is_shadowed),
            None,
        )

    def get_function_from_signature(self, function_signature: str) -> Optional["Function"]:
        """
            Return a function from a signature
        Args:
            function_signature (str): signature of the function (without return statement)
        Returns:
            Function
        """
        return next(
            (
                f
                for f in self.functions
                if f.solidity_signature == function_signature and not f.is_shadowed
            ),
            None,
        )

    def get_modifier_from_signature(self, modifier_signature: str) -> Optional["Modifier"]:
        """
        Return a modifier from a signature

        :param modifier_signature:
        """
        return next(
            (m for m in self.modifiers if m.full_name == modifier_signature and not m.is_shadowed),
            None,
        )

    def get_function_from_name(self, name: str) -> Optional["Function"]:
        """
            Return a function from a name
        Args:
            name (str): name of the function (not the signature)
        Returns:
            Function
        """
        return next((f for f in self.functions if f.name == name), None)

    def get_function_from_canonical_name(self, canonical_name: str) -> Optional["Function"]:
        """
            Return a function from a canonical name (contract.signature())
        Args:
            canonical_name (str): canonical name of the function (without return statement)
        Returns:
            Function
        """
        return next((f for f in self.functions if f.canonical_name == canonical_name), None)

    def get_modifier_from_canonical_name(self, canonical_name: str) -> Optional["Modifier"]:
        """
            Return a modifier from a canonical name (contract.signature())
        Args:
            canonical_name (str): canonical name of the modifier
        Returns:
            Modifier
        """
        return next((m for m in self.modifiers if m.canonical_name == canonical_name), None)

    def get_state_variable_from_name(self, variable_name: str) -> Optional["StateVariable"]:
        """
        Return a state variable from a name

        :param variable_name:
        """
        return next((v for v in self.state_variables if v.name == variable_name), None)

    def get_state_variable_from_canonical_name(
        self, canonical_name: str
    ) -> Optional["StateVariable"]:
        """
            Return a state variable from a canonical_name
        Args:
            canonical_name (str): name of the variable
        Returns:
            StateVariable
        """
        return next((v for v in self.state_variables if v.canonical_name == canonical_name), None)

    def get_structure_from_name(self, structure_name: str) -> Optional["StructureContract"]:
        """
            Return a structure from a name
        Args:
            structure_name (str): name of the structure
        Returns:
            StructureContract
        """
        return next((st for st in self.structures if st.name == structure_name), None)

    def get_structure_from_canonical_name(
        self, structure_name: str
    ) -> Optional["StructureContract"]:
        """
            Return a structure from a canonical name
        Args:
            structure_name (str): canonical name of the structure
        Returns:
            StructureContract
        """
        return next((st for st in self.structures if st.canonical_name == structure_name), None)

    def get_event_from_signature(self, event_signature: str) -> Optional["Event"]:
        """
            Return an event from a signature
        Args:
            event_signature (str): signature of the event
        Returns:
            Event
        """
        return next((e for e in self.events if e.full_name == event_signature), None)

    def get_event_from_canonical_name(self, event_canonical_name: str) -> Optional["Event"]:
        """
            Return an event from a canonical name
        Args:
            event_canonical_name (str): name of the event
        Returns:
            Event
        """
        return next((e for e in self.events if e.canonical_name == event_canonical_name), None)

    def get_enum_from_name(self, enum_name: str) -> Optional["Enum"]:
        """
            Return an enum from a name
        Args:
            enum_name (str): name of the enum
        Returns:
            Enum
        """
        return next((e for e in self.enums if e.name == enum_name), None)

    def get_enum_from_canonical_name(self, enum_name: str) -> Optional["Enum"]:
        """
            Return an enum from a canonical name
        Args:
            enum_name (str): canonical name of the enum
        Returns:
            Enum
        """
        return next((e for e in self.enums if e.canonical_name == enum_name), None)

    def get_functions_overridden_by(self, function: "Function") -> List["Function"]:
        """
            Return the list of functions overridden by the function
        Args:
            (core.Function)
        Returns:
            list(core.Function)

        """
        return function.overrides

    # endregion
    ###################################################################################
    ###################################################################################
    # region Recursive getters
    ###################################################################################
    ###################################################################################

    @property
    def all_functions_called(self) -> List["Function"]:
        """
        list(Function): List of functions reachable from the contract
        Includes super, and private/internal functions not shadowed
        """
        from slither.slithir.operations import Operation

        if self._all_functions_called is None:
            all_functions = [f for f in self.functions + self.modifiers if not f.is_shadowed]  # type: ignore
            all_callss = [f.all_internal_calls() for f in all_functions] + [list(all_functions)]
            all_calls = [
                item.function if isinstance(item, Operation) else item
                for sublist in all_callss
                for item in sublist
            ]
            all_calls = list(set(all_calls))

            all_constructors = [c.constructor for c in self.inheritance if c.constructor]
            all_constructors = list(set(all_constructors))

            set_all_calls = set(all_calls + list(all_constructors))

            self._all_functions_called = [c for c in set_all_calls if isinstance(c, Function)]
        return self._all_functions_called

    @property
    def all_state_variables_written(self) -> List["StateVariable"]:
        """
        list(StateVariable): List all of the state variables written
        """
        all_state_variables_writtens = [
            f.all_state_variables_written() for f in self.functions + self.modifiers  # type: ignore
        ]
        all_state_variables_written = [
            item for sublist in all_state_variables_writtens for item in sublist
        ]
        return list(set(all_state_variables_written))

    @property
    def all_state_variables_read(self) -> List["StateVariable"]:
        """
        list(StateVariable): List all of the state variables read
        """
        all_state_variables_reads = [
            f.all_state_variables_read() for f in self.functions + self.modifiers  # type: ignore
        ]
        all_state_variables_read = [
            item for sublist in all_state_variables_reads for item in sublist
        ]
        return list(set(all_state_variables_read))

    @property
    def all_library_calls(self) -> List["LibraryCall"]:
        """
        list(LibraryCall): List all of the libraries func called
        """
        all_high_level_callss = [f.all_library_calls() for f in self.functions + self.modifiers]  # type: ignore
        all_high_level_calls = [item for sublist in all_high_level_callss for item in sublist]
        return list(set(all_high_level_calls))

    @property
    def all_high_level_calls(self) -> List[Tuple["Contract", "HighLevelCall"]]:
        """
        list(Tuple("Contract", "HighLevelCall")): List all of the external high level calls
        """
        all_high_level_callss = [f.all_high_level_calls() for f in self.functions + self.modifiers]  # type: ignore
        all_high_level_calls = [item for sublist in all_high_level_callss for item in sublist]
        return list(set(all_high_level_calls))

    # endregion
    ###################################################################################
    ###################################################################################
    # region Summary information
    ###################################################################################
    ###################################################################################

    def get_summary(
        self, include_shadowed: bool = True
    ) -> Tuple[str, List[str], List[str], List, List]:
        """Return the function summary

        :param include_shadowed: boolean to indicate if shadowed functions should be included (default True)
        Returns:
            (str, list, list, list, list): (name, inheritance, variables, fuction summaries, modifier summaries)
        """
        func_summaries = [
            f.get_summary() for f in self.functions if (not f.is_shadowed or include_shadowed)
        ]
        modif_summaries = [
            f.get_summary() for f in self.modifiers if (not f.is_shadowed or include_shadowed)
        ]
        return (
            self.name,
            [str(x) for x in self.inheritance],
            [str(x) for x in self.variables],
            func_summaries,
            modif_summaries,
        )

    def is_signature_only(self) -> bool:
        """Detect if the contract has only abstract functions

        Returns:
            bool: true if the function are abstract functions
        """
        return all((not f.is_implemented) for f in self.functions)

    # endregion
    ###################################################################################
    ###################################################################################
    # region ERC conformance
    ###################################################################################
    ###################################################################################

    def ercs(self) -> List[str]:
        """
        Return the ERC implemented
        :return: list of string
        """
        all_erc = [
            ("ERC20", self.is_erc20),
            ("ERC165", self.is_erc165),
            ("ERC1820", self.is_erc1820),
            ("ERC223", self.is_erc223),
            ("ERC721", self.is_erc721),
            ("ERC777", self.is_erc777),
            ("ERC2612", self.is_erc2612),
            ("ERC1363", self.is_erc1363),
            ("ERC4626", self.is_erc4626),
        ]

        return [erc for erc, is_erc in all_erc if is_erc()]

    def is_erc20(self) -> bool:
        """
            Check if the contract is an erc20 token

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc20
        """
        full_names = self.functions_signatures
        return all(s in full_names for s in ERC20_signatures)

    def is_erc165(self) -> bool:
        """
            Check if the contract is an erc165 token

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc165
        """
        full_names = self.functions_signatures
        return all(s in full_names for s in ERC165_signatures)

    def is_erc1820(self) -> bool:
        """
            Check if the contract is an erc1820

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc165
        """
        full_names = self.functions_signatures
        return all(s in full_names for s in ERC1820_signatures)

    def is_erc223(self) -> bool:
        """
            Check if the contract is an erc223 token

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc223
        """
        full_names = self.functions_signatures
        return all(s in full_names for s in ERC223_signatures)

    def is_erc721(self) -> bool:
        """
            Check if the contract is an erc721 token

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc721
        """
        full_names = self.functions_signatures
        return all(s in full_names for s in ERC721_signatures)

    def is_erc1967(self) -> bool:
        """
            Check if the contract is an erc1967 proxy

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc1967 proxy
        """
        full_names = self.functions_signatures
        return all(s in full_names for s in ERC1967_signatures)
        
    def is_erc777(self) -> bool:
        """
            Check if the contract is an erc777

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc165
        """
        full_names = self.functions_signatures
        return all(s in full_names for s in ERC777_signatures)

    def is_erc1155(self) -> bool:
        """
            Check if the contract is an erc1155

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc1155
        """
        full_names = self.functions_signatures
        return all(s in full_names for s in ERC1155_signatures)

    def is_erc4626(self) -> bool:
        """
            Check if the contract is an erc4626

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc4626
        """
        full_names = self.functions_signatures
        return all(s in full_names for s in ERC4626_signatures)

    def is_erc2612(self) -> bool:
        """
            Check if the contract is an erc2612

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc2612
        """
        full_names = self.functions_signatures
        return all(s in full_names for s in ERC2612_signatures)

    def is_erc1363(self) -> bool:
        """
            Check if the contract is an erc1363

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc1363
        """
        full_names = self.functions_signatures
        return all(s in full_names for s in ERC1363_signatures)

    def is_erc4524(self) -> bool:
        """
            Check if the contract is an erc4524

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc4524
        """
        full_names = self.functions_signatures
        return all(s in full_names for s in ERC4524_signatures)

    @property
    def is_token(self) -> bool:
        """
        Check if the contract follows one of the standard ERC token
        :return:
        """
        return (
            self.is_erc20()
            or self.is_erc721()
            or self.is_erc165()
            or self.is_erc223()
            or self.is_erc777()
            or self.is_erc1155()
        )

    def is_possible_erc20(self) -> bool:
        """
        Checks if the provided contract could be attempting to implement ERC20 standards.

        :return: Returns a boolean indicating if the provided contract met the token standard.
        """
        # We do not check for all the functions, as name(), symbol(), might give too many FPs
        full_names = self.functions_signatures
        return (
            "transfer(address,uint256)" in full_names
            or "transferFrom(address,address,uint256)" in full_names
            or "approve(address,uint256)" in full_names
        )

    def is_possible_erc721(self) -> bool:
        """
        Checks if the provided contract could be attempting to implement ERC721 standards.

        :return: Returns a boolean indicating if the provided contract met the token standard.
        """
        # We do not check for all the functions, as name(), symbol(), might give too many FPs
        full_names = self.functions_signatures
        return (
            "ownerOf(uint256)" in full_names
            or "safeTransferFrom(address,address,uint256,bytes)" in full_names
            or "safeTransferFrom(address,address,uint256)" in full_names
            or "setApprovalForAll(address,bool)" in full_names
            or "getApproved(uint256)" in full_names
            or "isApprovedForAll(address,address)" in full_names
        )

    @property
    def is_possible_token(self) -> bool:
        """
        Check if the contract is a potential token (it might not implement all the functions)
        :return:
        """
        return self.is_possible_erc20() or self.is_possible_erc721()

    # endregion
    ###################################################################################
    ###################################################################################
    # region Dependencies
    ###################################################################################
    ###################################################################################

    def is_from_dependency(self) -> bool:
        return self.compilation_unit.core.crytic_compile.is_dependency(
            self.source_mapping.filename.absolute
        )

    # endregion
    ###################################################################################
    ###################################################################################
    # region Test
    ###################################################################################
    ###################################################################################

    @property
    def is_truffle_migration(self) -> bool:
        """
        Return true if the contract is the Migrations contract needed for Truffle
        :return:
        """
        if self.compilation_unit.core.crytic_compile.platform == PlatformType.TRUFFLE:
            if self.name == "Migrations":
                paths = Path(self.source_mapping.filename.absolute).parts
                if len(paths) >= 2:
                    return paths[-2] == "contracts" and paths[-1] == "migrations.sol"
        return False

    @property
    def is_test(self) -> bool:
        return is_test_contract(self) or self.is_truffle_migration  # type: ignore

    # endregion
    ###################################################################################
    ###################################################################################
    # region Function analyses
    ###################################################################################
    ###################################################################################

    def update_read_write_using_ssa(self) -> None:
        for function in self.functions + list(self.modifiers):
            function.update_read_write_using_ssa()

    # endregion
    ###################################################################################
    ###################################################################################
    # region Upgradeability
    ###################################################################################
    ###################################################################################

    @property
    def is_upgradeable(self) -> bool:
        if self._is_upgradeable is None:
            self._is_upgradeable = False
            if self.is_upgradeable_proxy:
                return False
            initializable = self.file_scope.get_contract_from_name("Initializable")
            if initializable:
                if initializable in self.inheritance:
                    self._is_upgradeable = True
            else:
                for contract in self.inheritance + [self]:
                    # This might lead to false positive
                    # Not sure why pylint is having a trouble here
                    # pylint: disable=no-member
                    lower_name = contract.name.lower()
                    if "upgradeable" in lower_name or "upgradable" in lower_name:
                        self._is_upgradeable = True
                        break
                    if "initializable" in lower_name:
                        self._is_upgradeable = True
                        break
        return self._is_upgradeable

    @is_upgradeable.setter
    def is_upgradeable(self, upgradeable: bool) -> None:
        self._is_upgradeable = upgradeable

    @property
    def is_upgradeable_proxy(self) -> bool:
        """
        Determines if a proxy contract can be upgraded, i.e. if there's an implementation address setter for upgrading

        :return: True if an implementation setter is found, or if the implementation getter suggests upgradeability
        """
        from slither.core.cfg.node import NodeType
        from slither.core.variables.state_variable import StateVariable
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.variables.structure_variable import StructureVariable
        from slither.core.declarations.function_contract import FunctionContract
        from slither.core.expressions.type_conversion import TypeConversion
        from slither.core.expressions.call_expression import CallExpression
        from slither.core.solidity_types.user_defined_type import UserDefinedType
        from slither.core.expressions.member_access import MemberAccess
        from slither.core.expressions.identifier import Identifier
        from slither.core.expressions.literal import Literal

        if self._is_upgradeable_proxy is None:
            self._is_upgradeable_proxy = False
            self._is_upgradeable_proxy_confirmed = False
            # calling self.is_proxy returns True or False, and should also set self._delegates_to in the process
            if self.is_proxy and self._delegate_variable is not None:
                
                # if the destination is a constant or immutable, return false
                if self._delegate_variable.is_constant or self._delegate_variable.is_immutable:
                    if self._proxy_impl_slot is None or self._proxy_impl_slot != self._delegate_variable:
                        self._is_upgradeable_proxy = False
                        return False
                # if the destination is hard-coded, return false
                if isinstance(self._delegate_variable.expression, Literal) and \
                        self._delegate_variable != self._proxy_impl_slot:
                    self._is_upgradeable_proxy = False
                    return False

                # self._delegate_variable should ideally be a StateVariable,
                # but it may be a LocalVariable if cross-contract analysis failed to find its source
                if isinstance(self._delegate_variable, LocalVariable):
                    if self.handle_local_delegate_from_call_exp():
                        return self._is_upgradeable_proxy

                # Now find setter in the contract. If we succeed, then the contract is upgradeable.
                # It is possible for self._proxy_impl_setter to already be found by this point.
                if self._proxy_impl_setter is None:
                    # Case: delegate is StateVariable declared in a different contract
                    if isinstance(self._delegate_variable, StateVariable) and self._delegate_variable.contract != self:
                        self.handle_delegate_state_var_different_contract()
                    # Case: delegate is LocalVariable in a function declared in a different contract
                    elif isinstance(self._delegate_variable, LocalVariable) and\
                            isinstance(self._delegate_variable.function, FunctionContract) and\
                            self._delegate_variable.function.contract != self:
                        self.handle_delegate_local_var_different_contract()
                    # Default case: look for setter in this contract
                    if self._proxy_impl_setter is None:
                        (self._proxy_impl_setter,
                         self._delegate_variable) = self.find_setter_in_contract(self, self._delegate_variable,
                                                                                 self._proxy_impl_slot)
                if self._proxy_impl_setter is not None:
                    # Setter is found, and upgradeability confirmed
                    self._is_upgradeable_proxy = True
                    self._is_upgradeable_proxy_confirmed = True
                
                # then find getter
                if self._proxy_impl_getter is None:
                    if isinstance(self._delegate_variable, StateVariable) and self._delegate_variable.contract != self:
                        self._proxy_impl_getter = self.find_getter_in_contract(self._delegate_variable.contract,
                                                                               self._delegate_variable)
                    if self._proxy_impl_getter is None:
                        self._proxy_impl_getter = self.find_getter_in_contract(self, self._delegate_variable)
                
                # if both setter and getter can be found, then return true
                # Otherwise, at least the getter's return is non-constant
                if self._proxy_impl_getter is not None:
                    if self._proxy_impl_setter is not None:
                        self._is_upgradeable_proxy = True
                        self._is_upgradeable_proxy_confirmed = True
                    else:
                        self._is_upgradeable_proxy = self.getter_return_is_non_constant()
                    return self._is_upgradeable_proxy
                else:
                    if self.handle_missing_getter():
                        return self._is_upgradeable_proxy
        return self._is_upgradeable_proxy

    @property
    def is_proxy(self) -> bool:
        """
        Checks for 'delegatecall' in the fallback function CFG, setting self._is_proxy = True if found.
        Also tries to set self._delegates_to: Variable in the process.

        :return: True if 'delegatecall' is found in fallback function, otherwise False
        """
        from slither.core.cfg.node import NodeType

        if self._is_proxy is None:
            self._is_proxy = False

            if self.fallback_function is None:
                return self._is_proxy

            self._delegate_variable = None
            for node in self.fallback_function.all_nodes():
                # first try to find a delegetecall in non-assembly code region
                is_proxy, self._delegate_variable = self.find_delegatecall_in_ir(node)
                if not self._is_proxy:
                    self._is_proxy = is_proxy
                if self._is_proxy and self._delegate_variable is not None:
                    break

                # then try to find delegatecall in assembly region
                if node.type == NodeType.ASSEMBLY:
                    """
                    Calls self.find_delegatecall_in_asm to search in an assembly CFG node.
                    That method cannot always find the delegates_to Variable for solidity versions >= 0.6.0
                    """
                    if node.inline_asm:
                        is_proxy, self._delegate_variable = self.find_delegatecall_in_asm(node.inline_asm,
                                                                                          node.function)
                        if not is_proxy:
                            is_proxy, self._delegate_variable = self.find_delegatecall_in_asm(node.inline_asm,
                                                                                              node.function,
                                                                                              include_call=True)
                        if not self._is_proxy:
                            self._is_proxy = is_proxy
                        if self._is_proxy and (self._delegate_variable is not None
                                               or self._proxy_impl_slot is not None):
                            break
                elif node.type == NodeType.EXPRESSION:
                    is_proxy, self._delegate_variable = self.find_delegatecall_in_exp_node(node)
                    if not self._is_proxy:
                        self._is_proxy = is_proxy
                    if self._is_proxy and (self._delegate_variable is not None
                                           or self._proxy_impl_slot is not None):
                        break
            if self.is_proxy and self._delegate_variable is None and self._proxy_impl_slot is not None:
                self._delegate_variable = self._proxy_impl_slot
        return self._is_proxy

    """
    Getters for attributes set by self.is_proxy and self.is_upgradeable_proxy
    """
    @property
    def delegate_variable(self) -> Optional["Variable"]:
        if self.is_proxy:
            return self._delegate_variable
        return self._delegate_variable

    @property
    def proxy_implementation_setter(self) -> Optional["FunctionContract"]:
        if self.is_upgradeable_proxy:
            return self._proxy_impl_setter
        return self._proxy_impl_setter

    @property
    def proxy_implementation_getter(self) -> Optional["FunctionContract"]:
        if self.is_upgradeable_proxy:
            return self._proxy_impl_getter
        return self._proxy_impl_getter

    @property
    def proxy_impl_storage_offset(self) -> Optional["Variable"]:
        return self._proxy_impl_slot

    @property
    def is_upgradeable_proxy_confirmed(self) -> Optional[bool]:
        if self._is_upgradeable_proxy_confirmed is None:
            if self.is_upgradeable_proxy:
                return self._is_upgradeable_proxy_confirmed
        return self._is_upgradeable_proxy_confirmed

    @property
    def uses_call_not_delegatecall(self) -> bool:
        return self._uses_call_not_delegatecall

    def find_delegatecall_in_asm(
            self,
            inline_asm: Union[str, Dict],
            parent_func: Function,
            include_call=False):
        """
        Called by self.is_proxy to help find 'delegatecall' in an inline assembly block,
        as well as the address Variable which the 'delegatecall' targets.
        It is necessary to handle two separate cases, for contracts using Solidity versions
        < 0.6.0 and >= 0.6.0, due to a change in how assembly is represented after compiling,
        i.e. as an AST for versions >= 0.6.0 and as a simple string for earlier versions.

        :param: inline_asm: The assembly code as either a string or an AST, depending on the solidity version
        :param: parent_func: The function associated with the assembly node (maybe another function called by fallback)
        :return: True if delegatecall is found, plus Variable delegates_to (if found)
        """

        delegates_to: Optional[Variable] = None
        asm_split = None

        if "AST" in inline_asm and isinstance(inline_asm, Dict):
            is_proxy, dest = Contract.find_delegatecall_in_asm_ast(inline_asm, include_call)
        else:
            is_proxy, dest, asm_split, delegates_to = self.find_delegatecall_in_asm_str(inline_asm,
                                                                                        parent_func,
                                                                                        include_call)
        if is_proxy and delegates_to is None and dest is not None:
            """
            Now that we extracted the name of the address variable passed as the second parameter to delegatecall, 
            we need to find the correct Variable object to ultimately assign to self._delegates_to.
            """
            if "_fallback_asm" in dest:
                dest = dest.split("_fallback_asm")[0]
            delegates_to = self.find_delegate_variable_from_name(dest, parent_func)
            if delegates_to is None and asm_split is not None:
                delegates_to = self.find_delegate_sloaded_from_hardcoded_slot(asm_split, dest, parent_func)
        return is_proxy, delegates_to

    @staticmethod
    def find_delegatecall_in_asm_ast(
            inline_asm: Union[str, Dict],
            include_call: bool
    ) -> (bool, str):
        is_proxy = False
        dest: Optional[Union[str, dict]] = None

        """
        inline_asm is a Yul AST for Solidity versions >= 0.6.0
        see tests/proxies/ExampleYulAST.txt for an example
        """
        for statement in inline_asm["AST"]["statements"]:
            if statement["nodeType"] == "YulExpressionStatement":
                statement = statement["expression"]
            if statement["nodeType"] == "YulVariableDeclaration":
                statement = statement["value"]
            if statement["nodeType"] == "YulFunctionCall":
                if statement["functionName"]["name"] == "delegatecall" or (include_call and
                                                                           statement["functionName"]["name"] == "call"):
                    is_proxy = True
                    args = statement["arguments"]
                    dest = args[1]
                    if dest["nodeType"] == "YulIdentifier":
                        dest = dest["name"]
                    break
        return is_proxy, dest

    def find_delegatecall_in_asm_str(
            self,
            inline_asm: Union[str, Dict],
            parent_func: Function,
            include_call=False
    ) -> (bool, str, list[str], Optional["Variable"]):
        from slither.core.expressions.identifier import Identifier
        from slither.core.variables.state_variable import StateVariable
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.solidity_types.elementary_type import ElementaryType

        is_proxy = False
        delegates_to: Optional["Variable"] = None
        """
        inline_asm is just a string for Solidity versions < 0.6.0.
        It contains the entire block of assembly code, so we can split it by line.
        """
        asm_split = inline_asm.split("\n")
        dest: Optional[str] = None
        for asm in asm_split:
            if "delegatecall" in asm or (include_call and "call(" in asm):
                if "delegatecall" not in inline_asm:
                    self._uses_call_not_delegatecall = True
                else:
                    # found delegatecall somewhere in full inline_asm
                    if "delegatecall" not in asm:
                        continue
                    else:
                        self._uses_call_not_delegatecall = False
                is_proxy = True  # Now look for the target of this delegatecall
                params = asm.split("call(")[1].split(", ")
                dest = params[1]
                # Target should be 2nd parameter, but 1st param might have 2 params
                # i.e. delegatecall(sub(gas, 10000), _dst, free_ptr, calldatasize, 0, 0)
                if dest.startswith("sload("):
                    # dest may not be correct, but we have found the storage slot
                    dest = dest.replace(")", "(").split("(")[1]
                    for v in parent_func.variables_read_or_written:
                        if v.name == dest:
                            if isinstance(v, LocalVariable) and v.expression is not None:
                                e = v.expression
                                if isinstance(e, Identifier) and isinstance(e.value, StateVariable):
                                    v = e.value
                                    """
                                    Fall through, use constant storage slot as delegates_to and proxy_impl_slot
                                    """
                            if isinstance(v, StateVariable) and v.is_constant:
                                # slot = str(v.expression)
                                # delegates_to = LocalVariable()
                                # delegates_to.set_type(ElementaryType("address"))
                                # delegates_to.name = dest
                                # delegates_to.set_location(slot)
                                delegates_to = v
                                self._proxy_impl_slot = v  # and also as proxy_impl_slot
                if dest.endswith(")"):
                    dest = params[2]
                break
        return is_proxy, dest, asm_split, delegates_to

    def find_delegate_variable_from_name(
            self,
            dest: str,
            parent_func: Function
    ) -> Optional["Variable"]:
        """
        Called by find_delegatecall_in_asm, which can only extract the name of the destination variable, not the object.
        Looks in every possible place for a Variable object with exactly the same name as extracted.
        If it's a state variable, our work is done here.
        But it may also be a local variable declared within the function, or a parameter declared in its signature.
        In which case, we need to track it further, but at that point we can stop using names.

        :param dest: The name of the delegatecall destination, as a string extracted from assembly
        :param parent_func: The Function in which we found the ASSEMBLY Node containing delegatecall
        :return: the corresponding Variable object, if found
        """
        from slither.core.variables.variable import Variable
        from slither.core.solidity_types.elementary_type import ElementaryType

        delegate = None
        if len(dest) == 42 and dest.startswith("0x"):
            addr = Literal(dest, ElementaryType("address"))
            delegate = Variable()
            delegate.expression = addr
            delegate.type = ElementaryType("address")
            delegate.name = dest
            return delegate
        for sv in self.state_variables:
            if sv.name == dest:
                delegate = sv
                return delegate
        delegate = self.find_local_delegate_from_name(dest, parent_func)
        if delegate is not None:
            return delegate
        delegate = self.find_parameter_delegate_from_name(dest, parent_func)
        if delegate is not None:
            return delegate
        if parent_func.contains_assembly and delegate is None:  # and self._proxy_impl_slot is not None:
            delegate = self.find_delegate_in_asm_from_name(dest, parent_func)
            if delegate is not None:
                return delegate
        return delegate

    def find_local_delegate_from_name(
            self,
            dest: str,
            parent_func: Function
    ) -> Optional["Variable"]:
        """
        Extension of self.find_delegate_variable_by_name()
        Used to handle searching for matching local variables and tracking them to their source.

        :param dest: The name of the delegatecall destination, as a string extracted from assembly
        :param parent_func: The Function in which we found the ASSEMBLY Node containing delegatecall
        :return: the corresponding Variable object, if found
        """
        from slither.core.cfg.node import NodeType
        from slither.core.variables.variable import Variable
        from slither.core.variables.state_variable import StateVariable
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.expressions.type_conversion import TypeConversion
        from slither.core.expressions.call_expression import CallExpression
        from slither.core.expressions.assignment_operation import AssignmentOperation
        from slither.core.expressions.index_access import IndexAccess
        from slither.core.expressions.member_access import MemberAccess
        from slither.core.expressions.identifier import Identifier

        delegate = None
        for lv in parent_func.local_variables:
            if delegate is not None or self._proxy_impl_slot is not None:
                return delegate
            if lv.name == dest:
                # TODO: eliminate dependence on variable name for Diamond handling
                if lv.name == "facet":
                    delegate = lv
                    return delegate
                if lv.expression is not None:
                    exp = self.unwrap_assignment_member_access(lv.expression)
                    if isinstance(exp, IndexAccess):
                        exp = exp.expression_left
                        # Fall through
                    if isinstance(exp, Identifier) and isinstance(exp.value, StateVariable):
                        delegate = exp.value
                        return delegate
                    elif isinstance(exp, CallExpression):
                        """
                        Must be the getter, but we still need a variable
                        """
                        delegate = self.find_delegate_from_call_exp(exp, lv)
                        return delegate
                    if isinstance(exp, MemberAccess):
                        delegate = self.find_delegate_from_member_access(exp, lv)
                        if delegate is None:
                            delegate = lv
                        return delegate
                else:
                    # No expression found, so look for assignment operation
                    delegate = self.find_local_variable_assignment(lv, parent_func)
        return delegate

    def find_local_variable_assignment(
        self, lv: "LocalVariable", parent_func: Function
    ) -> Optional["Variable"]:
        from slither.core.cfg.node import NodeType
        from slither.core.variables.variable import Variable
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.expressions.call_expression import CallExpression
        from slither.core.expressions.identifier import Identifier

        delegate = None
        for node in parent_func.all_nodes():
            if node.type in (NodeType.EXPRESSION, NodeType.VARIABLE):
                exp = Contract.unwrap_assignment_member_access(node.expression)
                if isinstance(exp, CallExpression):
                    if str(exp.called) == "sload(uint256)":
                        delegate = lv
                        arg = exp.arguments[0]
                        if isinstance(arg, Identifier):
                            if (
                                isinstance(arg.value, LocalVariable)
                                and arg.value.expression is not None
                                and isinstance(arg.value.expression, Identifier)
                            ):
                                arg = arg.value.expression
                            if isinstance(arg.value, Variable) and arg.value.is_constant:
                                self._proxy_impl_slot = arg.value
                                break
                    else:
                        delegate = self.find_delegate_from_call_exp(exp, lv)
        return delegate

    def find_parameter_delegate_from_name(
            self,
            dest: str,
            parent_func: Function
    ) -> Optional["Variable"]:
        """
        Extension of self.find_delegate_variable_by_name()
        Used to handle searching for matching parameter variables and tracking them to their source.

        :param dest: The name of the delegatecall destination, as a string extracted from assembly
        :param parent_func: The Function in which we found the ASSEMBLY Node containing delegatecall
        :return: the corresponding Variable object, if found
        """
        from slither.core.cfg.node import NodeType
        from slither.core.variables.state_variable import StateVariable
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.expressions.call_expression import CallExpression
        from slither.core.expressions.assignment_operation import AssignmentOperation
        from slither.core.expressions.index_access import IndexAccess
        from slither.core.expressions.member_access import MemberAccess
        from slither.core.expressions.identifier import Identifier

        delegate = None
        for idx, pv in enumerate(parent_func.parameters):
            if pv.name == dest:
                # delegate = pv
                for node in self.fallback_function.all_nodes():
                    if node.type == NodeType.EXPRESSION or node.type == NodeType.VARIABLE:
                        exp = self.unwrap_assignment_member_access(node.expression)
                        if isinstance(exp, CallExpression):
                            called = exp.called
                            if isinstance(called, MemberAccess):
                                if str(called) == f"{parent_func.contract.name}.{parent_func.name}":
                                    var = exp.arguments[idx]
                                    if isinstance(var, Identifier) and isinstance(var.value, StateVariable):
                                        delegate = var.value
                                        break
                            if isinstance(called, Identifier) and called.value == parent_func:
                                arg = exp.arguments[idx]
                                if isinstance(arg, Identifier):
                                    v = arg.value
                                    if isinstance(v, StateVariable):
                                        delegate = v
                                        break
                                    elif isinstance(v, LocalVariable) and v.expression is not None:
                                        delegate = v
                                        exp = v.expression
                                        if isinstance(exp, Identifier) and isinstance(exp.value, StateVariable):
                                            delegate = exp.value
                                        elif isinstance(exp, CallExpression):
                                            called = exp.called
                                            _delegate = self.find_delegate_from_call_exp(exp, v)
                                            if _delegate is not None:
                                                delegate = _delegate
                                        break
                                elif isinstance(arg, CallExpression):
                                    called = exp.called
                                    _delegate = self.find_delegate_from_call_exp(arg, pv)
                                    if _delegate is not None:
                                        delegate = _delegate
                                        break
                                elif isinstance(arg, IndexAccess):
                                    if isinstance(arg.expression_left, Identifier):
                                        delegate = arg.expression_left.value
                                        delegate.expression = arg
                                    break
                break
        return delegate

    def find_delegate_in_asm_from_name(
            self,
            dest: str,
            parent_func: Function
    ) -> Optional["Variable"]:
        """
        Extension of self.find_delegate_variable_by_name()
        Used to handle searching for matching variables loaded in assembly using sload(),
        and determining which storage slot they are loaded from.

        :param dest: The name of the delegatecall destination, as a string extracted from assembly
        :param parent_func: The Function in which we found the ASSEMBLY Node containing delegatecall
        :return: the corresponding Variable object, if found
        """
        from slither.core.cfg.node import NodeType
        from slither.core.variables.variable import Variable
        from slither.core.variables.state_variable import StateVariable
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.solidity_types.elementary_type import ElementaryType
        from slither.core.declarations.contract_level import ContractLevel
        from slither.core.expressions.literal import Literal
        from slither.core.expressions.type_conversion import TypeConversion
        from slither.core.expressions.call_expression import CallExpression
        from slither.core.expressions.assignment_operation import AssignmentOperation
        from slither.core.expressions.index_access import IndexAccess
        from slither.core.expressions.member_access import MemberAccess
        from slither.core.expressions.identifier import Identifier

        delegate = None
        # If we still haven't found the delegate variable, and the function contains assembly, look for sload
        for node in parent_func.all_nodes():
            if node.type == NodeType.ASSEMBLY:
                if isinstance(node.inline_asm, str):
                    asm = node.inline_asm.split("\n")
                    for s in asm:
                        if f"{dest}" in s and ":=" in s:
                            if "sload" in s:
                                dest = s.replace(")", "(").split("(")[1]
                                if not dest.endswith("_slot"):
                                    slot_var = parent_func.get_local_variable_from_name(dest)
                                    if slot_var is not None and slot_var.expression is not None:
                                        slot_exp = slot_var.expression
                                        if isinstance(slot_exp, Identifier) and slot_exp.value.is_constant:
                                            self._proxy_impl_slot = slot_exp.value
                                break
                else:
                    asm = node.inline_asm
                    for statement in asm["AST"]["statements"]:
                        if statement["nodeType"] == "YulVariableDeclaration" \
                                and statement["variables"][0]["name"] == dest:
                            if statement["value"]["nodeType"] == "YulFunctionCall" \
                                    and statement["value"]["functionName"]["name"] == "and" \
                                    and statement["value"]["arguments"][0]["nodeType"] == "YulFunctionCall" \
                                    and statement["value"]["arguments"][0]["functionName"]["name"] == "sload":
                                statement["value"] = statement["value"]["arguments"][0]
                            if statement["value"]["nodeType"] == "YulFunctionCall" \
                                    and statement["value"]["functionName"]["name"] == "sload":
                                if statement["value"]["arguments"][0]["nodeType"] == "YulLiteral":
                                    slot = statement["value"]["arguments"][0]["value"]
                                    if len(slot) == 66 and slot.startswith("0x"):  # 32-bit memory address
                                        # delegate = LocalVariable()
                                        # delegate.set_type(ElementaryType("address"))
                                        # delegate.name = dest
                                        # delegate.set_location(slot)
                                        impl_slot = StateVariable()
                                        impl_slot.name = slot
                                        impl_slot.is_constant = True
                                        impl_slot.expression = Literal(slot, ElementaryType("bytes32"))
                                        impl_slot.set_type(ElementaryType("bytes32"))
                                        impl_slot.set_contract(node.function.contract
                                                               if isinstance(node.function, ContractLevel)
                                                               else self)
                                        self._proxy_impl_slot = impl_slot
                                        break
                                    elif slot == "0":
                                        delegate = self.state_variables_ordered[0]
                                elif statement["value"]["arguments"][0]["nodeType"] == "YulIdentifier":
                                    for sv in self.state_variables:
                                        if sv.name == statement["value"]["arguments"][0]["name"] and sv.is_constant:
                                            # slot = str(sv.expression)
                                            # delegate = LocalVariable()
                                            # delegate.set_type(ElementaryType("address"))
                                            # delegate.name = dest
                                            # delegate.set_location(slot)
                                            self._proxy_impl_slot = sv
        if delegate is None and dest.endswith("_slot"):
            delegate = self.find_delegate_variable_from_name(dest.replace('_slot', ''), parent_func)
        return delegate

    @staticmethod
    def unwrap_assignment_member_access(exp: "Expression"):
        from slither.core.expressions.assignment_operation import AssignmentOperation
        from slither.core.expressions.member_access import MemberAccess

        if isinstance(exp, AssignmentOperation):
            exp = exp.expression_right
        if isinstance(exp, MemberAccess):
            exp = exp.expression
        return exp

    @staticmethod
    def unwrap_type_conversion(exp: "Expression"):
        from slither.core.expressions.type_conversion import TypeConversion

        while isinstance(exp, TypeConversion):
            exp = exp.expression
        return exp

    def find_delegate_from_call_exp(self, exp, var) -> Optional["Variable"]:
        """
        Called by self.find_delegate_variable_from_name
        Having found a LocalVariable matching the destination name extracted from the delegatecall,
        we know that the value of the local variable is gotten by the given CallExpression.
        Therefore, we are interested in tracking the origin of the value returned by the Function being called.
        There are 2 ways to return values from a function in Solidity (though they may be mixed, leading to case 3):
            1 - explicitly assigning values to named return variables, i.e.
                function _implementation() internal view returns (address impl) {
                    bytes32 slot = IMPLEMENTATION_SLOT;
                    assembly {
                        impl := sload(slot)
                    }
                }
            2 - returning values directly using a return statement (in which case variable names may be omitted), i.e.
                function implementation() public view returns (address) {
                    return getAppBase(appId());
                }
            3 - return variable is given a name, but is not assigned a value, instead using a return statement, i.e.
                function _implementation() internal view virtual override returns (address impl) {
                    return ERC1967Upgrade._getImplementation();
                }
        Given this fact, without knowing anything about the pattern, we know that we must approach this in 1 of 2 ways:
            1 - If the function has no RETURN node, then take the named return Variable object and look for where it is
                assigned a value
            2 - Otherwise, find the RETURN node at the end of the function's CFG, determine which Variable
                object it is returning, then look for where it is assigned a value
        For expediency, check #2 first

        :param exp: a CallExpression in which we want to find the source of the return value
        :param var: a Variable to fall back on if tracing it to it's source fails
        :return: the corresponding Variable object, if found
        """
        from slither.core.cfg.node import NodeType
        from slither.core.variables.variable import Variable
        from slither.core.variables.state_variable import StateVariable
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.expressions.tuple_expression import TupleExpression
        from slither.core.expressions.call_expression import CallExpression
        from slither.core.expressions.member_access import MemberAccess
        from slither.core.expressions.index_access import IndexAccess
        from slither.core.expressions.assignment_operation import AssignmentOperation
        from slither.core.expressions.type_conversion import TypeConversion
        from slither.core.expressions.identifier import Identifier
        from slither.core.expressions.literal import Literal
        from slither.core.solidity_types.elementary_type import ElementaryType
        from slither.core.declarations.function_contract import FunctionContract
        from slither.analyses.data_dependency import data_dependency

        delegate: Optional[Variable] = None
        func: Optional[Function] = None
        ret: Optional[Variable] = None
        if isinstance(exp, CallExpression):     # Guaranteed but type checking never hurts and helps IDE w autocomplete
            called = exp.called
            if isinstance(called, Identifier):
                val = called.value
                if isinstance(val, Function):   # Identifier.value is usually a Variable but here it's always a Function
                    func = val
            elif isinstance(called, MemberAccess):
                delegate = self.find_delegate_from_member_access(exp, var)
                return delegate
        if func is not None:
            if len(func.all_nodes()) == 0:
                # Sometimes Slither connects a CallExpression to an abstract function, missing the overriding function
                func = self.get_function_from_signature(func.full_name)
                while func is None:
                    for c in self.inheritance:
                        func = c.get_function_from_signature(func.full_name)
            ret = func.returns[0]
            # if ret.name is None or ret.name == "":
            # Case #2/3 - need to find RETURN node and the variable returned first
            ret_nodes = func.return_nodes()
            if ret_nodes is not None:
                for ret_node in ret_nodes:
                    if ret_node is not None:
                        rex = ret_node.expression
                        if var.expression is None:
                            var.expression = rex
                        if isinstance(rex, Identifier) and isinstance(rex.value, Variable):
                            ret = rex.value
                            if isinstance(ret, LocalVariable):
                                break
                        elif isinstance(rex, CallExpression):
                            called = rex.called
                            if isinstance(called, MemberAccess):
                                delegate = self.find_delegate_from_member_access(called, var)
                            elif isinstance(called, Identifier) and isinstance(called.value, FunctionContract) \
                                    and called.value.contract != self:
                                delegate = called.value.contract.find_delegate_from_call_exp(rex, var)
                            else:
                                delegate = self.find_delegate_from_call_exp(rex, var)
                            if delegate is None:
                                delegate = LocalVariable()
                                delegate.expression = rex
                            if delegate.name is None:
                                delegate.name = str(called)
                            if delegate.type is None:
                                delegate.type = ret.type
                            args = [arg.value for arg in exp.arguments if isinstance(arg, Identifier)]
                            for a in args:
                                if isinstance(a, StateVariable) and str(a.type) == "bytes32" and a.is_constant:
                                    self._proxy_impl_slot = a
                                    if delegate.name == str(called) and delegate.expression == rex:
                                        """ 
                                        If we constructed a LocalVariable from scratch above, but 
                                        then found the slot variable in the call expression arguments,
                                        it may be better just to use the fallback variable `var` which
                                        was assigned the value returned by the call expression.
                                        """
                                        delegate = var
                                    break
                            return delegate
                        elif isinstance(rex, IndexAccess):
                            left = rex.expression_left
                            if isinstance(left, Identifier) and isinstance(left.value, StateVariable):
                                delegate = left.value
            if ret.name is not None and ret_nodes is None:
                # Case #1 - return variable is named, so it's initialized in the entry point with no value assigned
                for n in func.all_nodes():
                    if n.type == NodeType.EXPRESSION:
                        e = n.expression
                        if isinstance(e, AssignmentOperation):
                            left = e.expression_left
                            right = e.expression_right
                            if isinstance(left, Identifier) and left.value == ret:
                                if isinstance(right, CallExpression):
                                    ret.expression = right
                                    if str(right.called) == "sload(uint256)":
                                        arg = right.arguments[0]
                                        if isinstance(arg, Identifier):
                                            v = arg.value
                                            if isinstance(v, Variable) and v.is_constant:
                                                self._proxy_impl_slot = v
                                                break
                                            elif isinstance(v, LocalVariable) and v.expression is not None:
                                                e = v.expression
                                                if isinstance(e, Identifier) and e.value.is_constant:
                                                    self._proxy_impl_slot = e.value
                                                    break
                                        elif isinstance(arg, Literal):
                                            slot_var = StateVariable()
                                            slot_var.name = str(arg.value)
                                            slot_var.type = ElementaryType("bytes32")
                                            slot_var.is_constant = True
                                            slot_var.expression = arg
                                            slot_var.set_contract(func.contract if isinstance(func, FunctionContract)
                                                                  else self)
                                            self._proxy_impl_slot = slot_var
                                            break
                                    elif str(right.called) == "abi.decode":
                                        arg = right.arguments[0]
                                        if isinstance(arg, Identifier):
                                            v = arg.value
                                            if v.expression is not None:
                                                ret.expression = v.expression
                                                delegate = ret
                                            else:
                                                for exp in func.expressions:
                                                    if isinstance(exp, AssignmentOperation):
                                                        if v.name in str(exp.expression_left):
                                                            ret.expression = exp.expression_right
                                                            delegate = ret
                                                            break
                                    else:
                                        delegate = self.find_delegate_from_call_exp(right, ret)
                                        right_called = right.called
                                        if delegate is None and isinstance(right_called, MemberAccess):
                                            member_access_exp = right_called.expression
                                            if isinstance(member_access_exp, TypeConversion):
                                                e = member_access_exp.expression
                                                if isinstance(e, Identifier) and str(e.value.type) == "address":
                                                    delegate = self.find_delegate_variable_from_name(e.value.name, func)
            if isinstance(ret, StateVariable):
                delegate = ret
            elif func.contains_assembly:
                for n in func.all_nodes():
                    if delegate is not None or self._proxy_impl_slot is not None:
                        break
                    if n.type == NodeType.ASSEMBLY and isinstance(n.inline_asm, str):
                        # only handle versions < 0.6.0 here - otherwise use EXPRESSION nodes
                        asm_split = n.inline_asm.split("\n")
                        for asm in asm_split:
                            if ret.name + " := sload(" in asm:
                                # Return value set by sload in asm: extract the name of the slot variable
                                slot_name = asm.split("sload(")[1].split(")")[0]
                                if slot_name.startswith("0x"):
                                    delegate = self.find_delegate_sloaded_from_hardcoded_slot(asm_split, ret.name, func)
                                    if delegate is not None:
                                        break
                                # Find the slot variable by its name
                                for v in func.variables_read_or_written:
                                    if v.name == slot_name:
                                        if isinstance(v, StateVariable) and v.is_constant:
                                            self._proxy_impl_slot = v
                                            break
                                        elif isinstance(v, LocalVariable) and v.expression is not None:
                                            e = v.expression
                                            if isinstance(e, Identifier) and e.value.is_constant:
                                                self._proxy_impl_slot = e.value
                                                break
                                break
                    elif n.type == NodeType.EXPRESSION and ret.name in str(n.expression):
                        # handle versions >= 0.6.0: we have expression nodes for assembly expressions
                        e = n.expression
                        if isinstance(e, AssignmentOperation):
                            left = e.expression_left
                            right = e.expression_right
                            if isinstance(left, Identifier) and left.value == ret:
                                if isinstance(right, CallExpression) and "sload" in str(right):
                                    arg = right.arguments[0]
                                    if isinstance(arg, Identifier):
                                        v = arg.value
                                        if isinstance(v, StateVariable) and v.is_constant:
                                            self._proxy_impl_slot = v
                                        elif isinstance(v, LocalVariable) and v.expression is not None:
                                            e = v.expression
                                            if isinstance(e, Identifier) and e.value.is_constant:
                                                self._proxy_impl_slot = e.value
                                    break
            elif isinstance(ret, LocalVariable):
                if ret.expression is not None:
                    e = ret.expression
                    if isinstance(e, CallExpression):
                        called = e.called
                        if isinstance(called, Identifier):
                            val = called.value
                            if isinstance(val, FunctionContract):
                                if val.contract != self:
                                    delegate = ret
                        elif isinstance(called, MemberAccess):
                            if str(called) == "abi.decode":
                                arg = e.arguments[0]
                                if isinstance(arg, Identifier):
                                    val = arg.value
                                    for n in func.all_nodes():
                                        if n.type == NodeType.EXPRESSION:
                                            e = n.expression
                                            if isinstance(e, AssignmentOperation):
                                                left = e.expression_left
                                                right = e.expression_right
                                                if isinstance(left, Identifier) and left.value == val:
                                                    ret.expression = right
                                                    break
                                                elif isinstance(left, TupleExpression):
                                                    for v in left.expressions:
                                                        if isinstance(v, Identifier) and v.value == val:
                                                            ret.expression = right
                                                            break
                                    e = ret.expression
                                    if isinstance(e, CallExpression) and isinstance(e.called, MemberAccess):
                                        delegate = self.find_delegate_from_member_access(e, var)
                            elif called.member_name == "call" or called.member_name == "staticcall":
                                _delegate = self.find_delegate_from_member_access(e, var)
                                if _delegate is not None:
                                    delegate = _delegate
                            else:
                                _delegate = self.find_delegate_from_member_access(called, var)
                                if _delegate is not None:
                                    delegate = _delegate
                    elif isinstance(e, IndexAccess):
                        left = e.expression_left
                        if isinstance(left, Identifier):
                            delegate = left.value
        return delegate

    def find_delegate_from_member_access(self, exp, var) -> Optional["Variable"]:
        """
        Called by self.find_delegate_from_call_exp
        Tries to find the correct delegate variable object, i.e. self._delegates_to, given
        a Member Access expression. A Member Access expression may represent a call to a
        function in another contract, so this method tries to find the associated contract
        in the compilation unit, and if found, tracks down the function that was called.

        :param exp: either a MemberAccess expression or a CallExpression containing a MemberAccess
        :param var: Variable which got its value from the MemberAccess, to be used if the source can't be found
        :return: the corresponding Variable object, if found
        """
        from slither.core.cfg.node import NodeType
        from slither.core.declarations.structure import Structure
        from slither.core.variables.state_variable import StateVariable
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.expressions.identifier import Identifier
        from slither.core.expressions.member_access import MemberAccess
        from slither.core.expressions.index_access import IndexAccess
        from slither.core.expressions.type_conversion import TypeConversion
        from slither.core.expressions.call_expression import CallExpression
        from slither.core.expressions.assignment_operation import AssignmentOperation
        from slither.core.solidity_types.user_defined_type import UserDefinedType
        from slither.core.solidity_types.elementary_type import ElementaryType

        delegate: Optional[Variable] = None
        contract: Optional[Contract] = None
        member_name = None
        args = None
        orig_exp = exp
        if isinstance(exp, CallExpression) and isinstance(exp.called, MemberAccess):
            args = exp.arguments
            exp = exp.called
        if isinstance(exp, MemberAccess):
            member_name = exp.member_name
            e = exp.expression
            if isinstance(e, CallExpression):
                called = e.called
                if isinstance(called, Identifier):
                    f = called.value
                    if isinstance(f, Function):
                        ret_node = f.return_node()
                        if ret_node is not None:
                            e = f.return_node().expression
                        else:
                            ret_val = f.returns[0]
                            e = Identifier(ret_val)
                elif isinstance(called, MemberAccess):
                    if isinstance(var, LocalVariable):
                        parent_func = var.function
                        for lib_call in parent_func.all_library_calls():
                            if f"{lib_call[0]}.{lib_call[1]}" == str(called):
                                if len(e.arguments) > 0 and isinstance(e.arguments[0], Identifier):
                                    val = e.arguments[0].value
                                    if (isinstance(val, StateVariable) and val.is_constant
                                            and str(val.type) == "bytes32"):
                                        slot = val
                                        delegate = slot
                                        self._proxy_impl_slot = slot
                                break
            if isinstance(e, TypeConversion) or isinstance(e, Identifier):
                ctype = e.type
                if isinstance(e, Identifier):
                    if isinstance(e.value, Contract):
                        ctype = UserDefinedType(e.value)
                    else:
                        ctype = e.value.type
                if isinstance(ctype, UserDefinedType) and isinstance(ctype.type, Contract) and ctype.type != self:
                    contract = ctype.type
                    interface = None
                    if contract.is_interface or (contract.get_function_from_name(member_name) is not None and
                                                 not contract.get_function_from_name(member_name).is_implemented):
                        interface = contract
                    for c in self.compilation_unit.contracts:
                        if c == interface:
                            continue
                        if interface in c.inheritance:
                            contract = c
                    if contract.is_interface:
                        for c in self.compilation_unit.contracts:
                            if c == contract:
                                continue
                            for f in c.functions:
                                if f.name == member_name and str(f.return_type) == "address":
                                    contract = c
                            for v in c.state_variables:
                                if v.name == member_name and "public" in v.visibility and "address" in str(v.type):
                                    contract = c
                        if contract.is_interface:
                            delegate = var
                            return delegate
                elif isinstance(ctype, UserDefinedType) and isinstance(ctype.type, Structure):
                    struct = ctype.type
                    if isinstance(struct, Structure):
                        try:
                            delegate = struct.elems[member_name]
                        except:
                            if struct.contract != self:
                                fn = struct.contract.get_function_from_name(member_name)
                                if fn is not None and fn.return_node() is not None:
                                    ret_node = fn.return_node()
                                    rex = ret_node.expression
                                    if isinstance(rex, IndexAccess):
                                        left = rex.expression_left
                                        if isinstance(left, MemberAccess):
                                            ex = left.expression
                                            if isinstance(ex, Identifier):
                                                v = ex.value
                                                t = v.type
                                                if isinstance(t, UserDefinedType) and t.type == struct:
                                                    delegate = struct.elems[left.member_name]
                elif isinstance(ctype, ElementaryType) and ctype.type == "address":
                    if member_name == "call" or member_name == "staticcall":
                        """
                        Implementation address comes from a call to an address w/o a specified
                        Contract type, so we must check each contract for the function called.
                        Trying to handle the tough case of Dharma's KeyRingUpgradeBeaconProxy.
                        """
                        arg = orig_exp.arguments[0]
                        if arg is None or str(arg) == "":
                            arg = "fallback"
                        for c in self.compilation_unit.contracts:
                            if c == self:
                                continue
                            if arg == "fallback":
                                fn = c.fallback_function
                            else:
                                fn = c.get_function_from_name(arg)
                            if fn is None:
                                continue
                            else:
                                if len(fn.returns) > 0:
                                    if str(fn.returns[0].type) == "address":
                                        ret = fn.returns[0]
                                        """
                                        This part doesn't apply to the FN I'm trying to solve,
                                        so I leave it unfinished for now.
                                        """
                                else:
                                    """
                                    This bit is pretty specific to the Dharma BeaconProxy and
                                    DharmaUpgradeBeacon, which uses its fallback as both the
                                    setter and getter for the implementation address.
                                    """
                                    for node in fn.all_nodes():
                                        if node.type == NodeType.ASSEMBLY:
                                            inline_asm = node.inline_asm
                                            if "sload" in inline_asm and "mstore" in inline_asm\
                                                    and "return" in inline_asm:
                                                self._proxy_impl_getter = fn
                                            if "sstore" in inline_asm:
                                                self._proxy_impl_setter = fn
        if contract is not None:
            for f in contract.functions:
                if f.name == member_name:
                    if f.is_implemented:
                        self._proxy_impl_getter = f
                    ret = f.returns[0]
                    ret_node = f.return_node()
                    if ret_node is not None:
                        e = ret_node.expression
                        if isinstance(e, Identifier):
                            ret = e.value
                        elif isinstance(e, MemberAccess):
                            ex = e.expression
                            if isinstance(ex, CallExpression):
                                called = ex.called
                                if isinstance(called, MemberAccess):
                                    if delegate is None:
                                        delegate: LocalVariable = LocalVariable()
                                        delegate.expression = e
                                        delegate.set_function(ret_node.function)
                                    if delegate.name is None:
                                        delegate.name = str(e)
                                    if delegate.type is None:
                                        delegate.type = ret.type
                                    args = [arg.value for arg in ex.arguments if isinstance(arg, Identifier)]
                                    for a in args:
                                        if str(a.type) == "bytes32" and a.is_constant:
                                            self._proxy_impl_slot = a
                                            break
                            elif isinstance(ex, IndexAccess):
                                e = ex  # Fall through
                        if isinstance(e, IndexAccess):
                            left = e.expression_left
                            if isinstance(left, Identifier):
                                if isinstance(left.value, StateVariable):
                                    delegate = left.value
                                    break
                                elif isinstance(left.value, LocalVariable):
                                    delegate = self.find_delegate_variable_from_name(left.value.name, ret_node.function)
                                    if delegate is not None:
                                        break
                    if isinstance(ret, StateVariable):
                        delegate = ret
                    elif isinstance(ret, LocalVariable):
                        if ret.expression is None:
                            for n in f.all_nodes():
                                if n.type == NodeType.EXPRESSION:
                                    e = n.expression
                                    if isinstance(e, AssignmentOperation):
                                        left = e.expression_left
                                        right = e.expression_right
                                        if isinstance(left, Identifier) and left.value == ret:
                                            ret.expression = right
                                elif n.type == NodeType.ASSEMBLY:
                                    # TODO: check for assignment inside of assembly
                                    asm = n.inline_asm
                        if ret.expression is not None:
                            e = ret.expression
                            if isinstance(e, Identifier) and isinstance(e.value, StateVariable):
                                delegate = e.value
                            elif isinstance(e, CallExpression):
                                delegate = contract.find_delegate_from_call_exp(e, ret)
            if delegate is None:
                for v in contract.state_variables:
                    if v.name == member_name and "public" in v.visibility and "address" in str(v.type):
                        delegate = v
                        break
        return delegate

    def find_delegate_sloaded_from_hardcoded_slot(
            self,
            asm_split: List[str],
            dest: str,
            parent_func: Function
    ) -> Optional["Variable"]:
        """
        Finally, here I am trying to handle the case where there are no variables at all in the proxy,
        except for one defined within the assembly block itself with the slot hardcoded as seen below.
        In such an instance, there is literally no Variable object to assign to self._delegates_to,
        so we attempt to create a new one if appropriate
        ex: /tests/proxies/EIP1822Token.sol
        function() external payable {
            assembly { // solium-disable-line
                let logic := sload(0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7)
                calldatacopy(0x0, 0x0, calldatasize)
                let success := delegatecall(sub(gas, 10000), logic, 0x0, calldatasize, 0, 0)
                ...
            }
        }

        :param asm_split: a List of strings representing each line of assembly code
        :param dest: the name of the delegatecall destination variable extracted from the assembly string
        :param parent_func: the function in which this assembly is found
        :return: the corresponding Variable object, if found
        """
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.variables.state_variable import StateVariable
        from slither.core.expressions.literal import Literal
        from slither.core.declarations.contract_level import ContractLevel
        from slither.core.solidity_types.elementary_type import ElementaryType

        delegates_to = None
        for asm in asm_split:
            if dest in asm and "sload(" in asm:
                slot = asm.split("sload(", 1)[1].split(")")[0]
                if len(slot) == 66 and slot.startswith("0x"):  # 32-bit memory address
                    # TODO: make sure we don't need to construct a LocalVariable from scratch anymore,
                    #       now that we're allowing self._delegate_variable to equal self._proxy_impl_slot
                    # delegates_to = LocalVariable()
                    # delegates_to.set_type(ElementaryType("address"))
                    # delegates_to.name = dest
                    # delegates_to.set_location(slot)
                    impl_slot = StateVariable()
                    impl_slot.name = slot
                    impl_slot.is_constant = True
                    impl_slot.expression = Literal(slot, ElementaryType("bytes32"))
                    impl_slot.set_type(ElementaryType("bytes32"))
                    impl_slot.set_contract(parent_func.contract
                                           if isinstance(parent_func, ContractLevel)
                                           else self)
                    self._proxy_impl_slot = impl_slot
                    break
                else:
                    delegates_to = self.find_delegate_variable_from_name(slot.strip("_slot"), parent_func)
        return delegates_to

    @staticmethod
    def find_delegatecall_in_ir(node):     # General enough to keep as is
        """
        Handles finding delegatecall outside an assembly block, as a LowLevelCall
        i.e. delegate.delegatecall(msg.data)  
        ex: tests/proxies/Delegation.sol (appears to have been written to demonstrate a vulnerability)

        :param node: a CFG Node object
        :return: boolean indicating if delegatecall was found, and the corresponding Variable object, if found
        """
        from slither.slithir.operations import LowLevelCall
        from slither.core.expressions.identifier import Identifier
        from slither.core.expressions.call_expression import CallExpression
        from slither.core.expressions.member_access import MemberAccess
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.declarations.contract_level import ContractLevel
        from slither.core.declarations.function_contract import FunctionContract
        from slither.slithir.variables.temporary import TemporaryVariable

        is_proxy = False
        delegate_to = None

        for ir in node.irs:
            if isinstance(ir, LowLevelCall):
                if ir.function_name == "delegatecall":
                    is_proxy = True
                    delegate_to = ir.destination
                    break
        if isinstance(delegate_to, LocalVariable):
            e = delegate_to.expression
            if e is not None:
                if isinstance(e, CallExpression) and isinstance(delegate_to, ContractLevel):
                    if isinstance(delegate_to.function, ContractLevel):
                        delegate_to = delegate_to.function.contract.find_delegate_from_call_exp(e, delegate_to)
                elif isinstance(e, MemberAccess) and isinstance(delegate_to, ContractLevel):
                    delegate_to = delegate_to.contract.find_delegate_from_member_access(e, delegate_to)
        elif isinstance(delegate_to, TemporaryVariable):
            exp = delegate_to.expression
            if isinstance(exp, CallExpression):
                called = exp.called
                if isinstance(called, Identifier):
                    func = called.value
                    if isinstance(func, FunctionContract):
                        if not func.is_implemented:
                            for f in node.function.contract.functions:
                                if f.name == func.name and f.is_implemented:
                                    func = f
                        delegate_to = func.contract.find_delegate_from_call_exp(exp, delegate_to)
        return is_proxy, delegate_to

    def find_delegatecall_in_exp_node(self, node):
        """
        For versions >= 0.6.0, in addition to Assembly nodes as seen above, it seems that 
        Slither creates Expression nodes for expressions within an inline assembly block.
        This is convenient, because sometimes self.find_delegatecall_in_asm fails to find 
        the target Variable self._delegates_to, so this serves as a fallback for such cases.
        ex: /tests/proxies/App2.sol (for comparison, /tests/proxies/App.sol is an earlier version)

        :param node: a CFG Node object
        :return: the corresponding Variable object, if found
        """
        from slither.core.expressions.expression import Expression
        from slither.core.expressions.assignment_operation import AssignmentOperation
        from slither.core.expressions.call_expression import CallExpression
        from slither.core.expressions.member_access import MemberAccess
        from slither.core.expressions.index_access import IndexAccess
        from slither.core.expressions.identifier import Identifier
        from slither.core.expressions.literal import Literal
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.variables.state_variable import StateVariable

        is_proxy = False
        delegate_to = None
        expression = node.expression
        if isinstance(expression, Expression):
            if isinstance(expression, AssignmentOperation):
                """
                Handles the common case like this: 
                let result := delegatecall(gas, implementation, 0, calldatasize, 0, 0)
                """
                expression = expression.expression_right
        if isinstance(expression, CallExpression):
            if "delegatecall" in str(expression.called):
                is_proxy = True
                if len(expression.arguments) > 1:
                    dest = expression.arguments[1]
                    if isinstance(dest, Identifier):
                        val = dest.value
                        if isinstance(val, StateVariable):
                            delegate_to = val
                        elif isinstance(val, LocalVariable):
                            exp = val.expression
                            if exp is not None:
                                if isinstance(exp, Identifier) and isinstance(exp.value, StateVariable):
                                    delegate_to = exp.value
                                elif isinstance(exp, CallExpression):
                                    delegate_to = self.find_delegate_from_call_exp(exp, val)
                                elif isinstance(exp, MemberAccess):
                                    exp = exp.expression
                                    if isinstance(exp, IndexAccess):
                                        exp = exp.expression_left
                                        if isinstance(exp, Identifier):
                                            delegate_to = val
                                        elif isinstance(exp, MemberAccess):
                                            exp = exp.expression
                                            if isinstance(exp, Identifier):
                                                delegate_to = val
                                elif isinstance(exp, Literal) and str(exp.type) == "address":
                                    delegate_to = val
                            else:
                                delegate_to = self.find_delegate_variable_from_name(val.name, node.function)
        return is_proxy, delegate_to

    def getter_return_is_non_constant(self) -> bool:
        """
        If we could only find the getter, but not the setter, make sure that the getter does not return
        a variable that can never be set (i.e. is practically constant, but not declared constant)
        Instead we would like to see if the getter returns the result of a call to another function,
        possibly a function in another contract.
        ex: in /tests/proxies/APMRegistry.sol, AppProxyPinned should not be identified as upgradeable,
            though AppProxyUpgradeable obviously should be
        """
        from slither.core.cfg.node import NodeType
        from slither.core.expressions.call_expression import CallExpression
        from slither.core.expressions.assignment_operation import AssignmentOperation
        from slither.core.expressions.member_access import MemberAccess
        from slither.core.expressions.identifier import Identifier
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.variables.state_variable import StateVariable
        from slither.analyses.data_dependency import data_dependency

        for node in self._proxy_impl_getter.all_nodes():
            exp = node.expression
            if node.type == NodeType.EXPRESSION and isinstance(exp, AssignmentOperation):
                left = exp.expression_left
                right = exp.expression_right
                if isinstance(left, Identifier) and left.value == self._delegate_variable:
                    if isinstance(right, Identifier) and right.value.is_constant:
                        self._is_upgradeable_proxy = False
                        return self._is_upgradeable_proxy
                    elif isinstance(right, CallExpression):
                        if "sload" in str(right):
                            slot = right.arguments[0]
                            if isinstance(slot, Identifier):
                                slot = slot.value
                                if slot.is_constant:
                                    self._proxy_impl_slot = slot
                                elif isinstance(slot, LocalVariable):
                                    for v in self.variables:
                                        if data_dependency.is_dependent(slot, v, node.function) and v.is_constant:
                                            self._proxy_impl_slot = v
                                            break
                        if self._proxy_impl_slot is not None and self._proxy_impl_setter is None:
                            for f in self.functions:
                                if f.contains_assembly:
                                    slot = None
                                    for n in f.all_nodes():
                                        if n.type == NodeType.EXPRESSION:
                                            e = n.expression
                                            if isinstance(e, AssignmentOperation):
                                                l = e.expression_left
                                                r = e.expression_right
                                                if isinstance(r, Identifier) and r.value == self._proxy_impl_slot:
                                                    slot = l.value
                                            elif isinstance(e, CallExpression) and str(e.called) == "sstore":
                                                if e.arguments[0] == slot or e.arguments[0] == self._proxy_impl_slot:
                                                    self._proxy_impl_setter = f
                                        elif n.type == NodeType.ASSEMBLY and n.inline_asm is not None:
                                            if "sstore(" + str(slot) in n.inline_asm \
                                                    or "sstore(" + str(self._proxy_impl_slot) in n.inline_asm:
                                                self._proxy_impl_setter = f
                        self._is_upgradeable_proxy = True
                        return self._is_upgradeable_proxy
                    elif isinstance(right, MemberAccess):
                        self._is_upgradeable_proxy = True
                        return self._is_upgradeable_proxy
            elif node.type == NodeType.RETURN:
                if isinstance(exp, CallExpression):
                    self._is_upgradeable_proxy = True
                    return self._is_upgradeable_proxy
        return self._is_upgradeable_proxy

    @staticmethod
    def find_getter_in_contract(
            contract: "Contract", 
            var_to_get: Union[str, "Variable"]
    ) -> Optional[Function]:
        """
        Tries to find the getter function for a given variable.
        Static because we can use this for cross-contract implementation setters, i.e. EIP 1822 Proxy/Proxiable

        :param contract: the Contract to look in
        :param var_to_get: the Variable to look for, or at least its name as a string
        :return: the function in contract which sets var_to_set, if found
        """
        from slither.core.cfg.node import NodeType
        from slither.core.variables.variable import Variable
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.expressions.identifier import Identifier
        from slither.core.expressions.index_access import IndexAccess
        from slither.core.expressions.member_access import MemberAccess
        from slither.core.expressions.call_expression import CallExpression
        from slither.core.expressions.assignment_operation import AssignmentOperation
        from slither.core.solidity_types.user_defined_type import UserDefinedType

        getter = None
        exp = (var_to_get.expression if isinstance(var_to_get, Variable) else None)
        for f in contract.functions:
            if contract._proxy_impl_getter is not None:
                getter = contract._proxy_impl_getter
                break
            if len(f.all_nodes()) == 0:
                continue
            if f.name is not None:
                if isinstance(exp, CallExpression) and len(f.all_nodes()) > 0:
                    if f.name == str(exp.called) or exp in f.expressions:
                        getter = f
                        break
            else:
                continue
            if not f.is_fallback and not f.is_constructor and not f.is_receive and "init" not in f.name.lower():
                # if f.visibility == "internal" or f.visibility == "private":
                #     continue
                if len(f.returns) > 0:
                    skip_f = False
                    for v in f.returns:
                        if v == var_to_get:
                            getter = f
                            break
                        if (isinstance(v.type, UserDefinedType) and isinstance(v.type.type, Contract)) \
                                or isinstance(v.type, Contract):
                            """ Not interested in functions that return a new Contract """
                            skip_f = True
                    if skip_f:
                        continue
                    for n in f.all_nodes():
                        if getter is not None:
                            break
                        if n.type == NodeType.RETURN and n.function == f:
                            """ Not interested in RETURN nodes in functions called by f """
                            e = n.expression
                            if isinstance(e, MemberAccess):
                                e = e.expression
                                """Fall through to below"""
                            if isinstance(e, IndexAccess):
                                if isinstance(exp, IndexAccess):
                                    if isinstance(e.expression_left, Identifier) and isinstance(exp.expression_left,
                                                                                                Identifier):
                                        if e.expression_left.value == exp.expression_left.value:
                                            getter = f
                                            break
                                else:
                                    e = e.expression_left
                                    """Fall through to below"""
                            if isinstance(e, Identifier) and e.value == var_to_get:
                                getter = f
                                break
                        if contract.proxy_impl_storage_offset is not None and f.contains_assembly:
                            slot = contract.proxy_impl_storage_offset
                            if n.type == NodeType.ASSEMBLY and isinstance(n.inline_asm, str) \
                                    and "sload(" in n.inline_asm:
                                slot_name = n.inline_asm.split("sload(")[1].split(")")[0]
                                if slot_name == slot.name:
                                    getter = f
                                    break
                                for v in n.function.variables_read_or_written:
                                    if v.name == slot_name and isinstance(v, LocalVariable) and v.expression is not None:
                                        e = v.expression
                                        if isinstance(e, Identifier) and e.value == slot:
                                            getter = f
                                            break
                            elif n.type == NodeType.EXPRESSION:
                                e = n.expression
                                if isinstance(e, AssignmentOperation):
                                    e = e.expression_right
                                if isinstance(e, CallExpression) and "sload" in str(e.called):
                                    e = e.arguments[0]
                                    if isinstance(e, Identifier):
                                        v = e.value
                                        if v == slot:
                                            getter = f
                                            break
                                        elif isinstance(v, LocalVariable) and v.expression is not None:
                                            e = v.expression
                                            if isinstance(e, Identifier) and e.value == slot:
                                                getter = f
                                                break
                    if getter is not None:
                        break
        return getter

    @staticmethod
    def find_setter_in_contract(
            contract: "Contract",
            var_to_set: Union[str, "Variable"],
            storage_slot: Optional["Variable"]
    ) -> (Optional[Function], Union[str, "Variable"]):
        """
        Tries to find the setter function for a given variable.
        Static because we can use this for cross-contract implementation setters, i.e. EIP 1822 Proxy/Proxiable

        :param contract: the Contract to look in
        :param var_to_set: the Variable to look for, or at least its name as a string
        :param storage_slot: an optional, constant variable containing a storage offset (for setting via sstore)
        :return: the function in contract which sets var_to_set, if found, and var_to_set, which may have been changed
        """
        from slither.core.cfg.node import NodeType
        from slither.core.variables.variable import Variable
        from slither.core.variables.state_variable import StateVariable
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.expressions.expression import Expression
        from slither.core.expressions.assignment_operation import AssignmentOperation, AssignmentOperationType
        from slither.core.expressions.call_expression import CallExpression
        from slither.core.expressions.member_access import MemberAccess
        from slither.core.expressions.index_access import IndexAccess
        from slither.core.expressions.identifier import Identifier

        setter = None
        assignment = None
        var_exp = (var_to_set.expression if isinstance(var_to_set, Variable) else None)
        for f in contract.functions_declared + contract.functions_inherited:
            if setter is not None:
                break
            if not f.is_fallback and not f.is_constructor and not f.is_receive \
                    and "init" not in f.name.lower() and "fallback" not in f.name.lower():  # avoid _fallback()
                if f.visibility == "internal" or f.visibility == "private":
                    continue
                # # Commented out because the remaining code can handle any cases this one would catch,
                # # but we need to check for an AssignmentOperation that writes to var_to_set
                # # in case we find that the value being written comes from a cross-contract call.
                # for v in f.variables_written:
                #     if isinstance(v, LocalVariable) and v in f.returns:
                #         continue
                #     elif isinstance(v, StateVariable):
                #         if str(var_to_set) == v.name:
                #             setter = f
                #             break
                for node in f.all_nodes():
                    if setter is not None:
                        break
                    if node.type == NodeType.ASSEMBLY:
                        inline = node.inline_asm
                        if isinstance(inline, str):
                            for asm in inline.split("\n"):
                                if "sstore" in asm:
                                    slot_name = asm.split("sstore(")[1].split(",")[0]
                                    written_name = name = asm.split("sstore(")[1].split(",")[1].split(")")[0].strip()
                                    if slot_name == str(storage_slot):
                                        setter = f
                                        break
                                    for v in node.function.variables_read_or_written:
                                        if v.name == slot_name:
                                            if v in [storage_slot, var_to_set]:
                                                setter = f
                                            elif isinstance(v, LocalVariable):
                                                exp = v.expression
                                                if isinstance(exp, Identifier) and exp.value in [storage_slot,
                                                                                                 var_to_set]:
                                                    setter = f
                                        elif v.name == written_name and isinstance(v, LocalVariable):
                                            exp = v.expression
                                            if isinstance(exp, AssignmentOperation):
                                                assignment = exp
                                            elif isinstance(exp, CallExpression) or isinstance(exp, MemberAccess):
                                                v_id = Identifier(v)
                                                assignment = AssignmentOperation(v_id, exp,
                                                                                 AssignmentOperationType.ASSIGN)
                                    if setter is not None:
                                        break
                    elif node.type == NodeType.EXPRESSION or node.type == NodeType.RETURN:
                        exp = node.expression
                        if isinstance(exp, CallExpression) and "sstore" in str(exp.called):
                            slot_arg = exp.arguments[0]
                            written_arg = exp.arguments[1]
                            if isinstance(slot_arg, Identifier):
                                v = slot_arg.value
                                if v in [storage_slot, var_to_set]:
                                    setter = f
                                elif isinstance(v, LocalVariable):
                                    exp = v.expression
                                    if isinstance(exp, Identifier) and exp.value in [storage_slot, var_to_set]:
                                        setter = f
                            elif storage_slot is not None and str(slot_arg) == storage_slot.name:
                                setter = f
                            if isinstance(written_arg, Identifier) and isinstance(written_arg.value, LocalVariable):
                                exp = written_arg.value.expression
                                if isinstance(exp, AssignmentOperation):
                                    assignment = exp
                                elif isinstance(exp, CallExpression) or isinstance(exp, MemberAccess):
                                    assignment = AssignmentOperation(written_arg, exp,
                                                                     AssignmentOperationType.ASSIGN)
                        elif isinstance(exp, AssignmentOperation):
                            left = exp.expression_left
                            if isinstance(left, MemberAccess):
                                member_of = left.expression
                                if isinstance(member_of, CallExpression):
                                    if var_to_set in [arg.value for arg in member_of.arguments
                                                      if isinstance(arg, Identifier)]:
                                        setter = f
                                        assignment = exp
                                    elif str(left) == var_to_set.name:
                                        setter = f
                                        assignment = exp
                            elif var_exp is not None:
                                if var_exp == left or str(var_exp) == str(left):   # Expression.__eq__() not implemented
                                    setter = f
                                    assignment = exp
                                elif isinstance(left, Identifier) and var_to_set == left.value:
                                    setter = f
                                    assignment = exp
                                elif isinstance(left, IndexAccess) and isinstance(var_exp, IndexAccess):
                                    if str(left.expression_left) == str(var_exp.expression_left):
                                        setter = f
                                        assignment = exp
                            elif isinstance(left, IndexAccess):
                                left = left.expression_left
                                if (isinstance(left, MemberAccess) and left.member_name == var_to_set.name) \
                                        or (isinstance(left, Identifier) and left.value == var_to_set):
                                    setter = f
                                    assignment = exp
                            elif str(left) == var_to_set.name:
                                setter = f
                                assignment = exp
        if setter is not None and assignment is not None:
            """
            Found setter in the given contract, and the AssignmentOperation doing the setting.
            But what is the new value that is being assigned, and where does it come from?
            Most likely it is just an address variable that comes from the setter's arguments,
            but the right side of the AssignmentOperation could include a CallExpression, which
            could be a cross-contract call. 
            For example (tests/proxies/ContributionTriggerRegistry.sol):
                function upgradeTo(uint256 _version) public {
                    require(msg.sender == address(registry),"ERR_ONLY_REGISTRERY_CAN_CALL");
                    _implementation = registry.getVersion(_version);
                }
            In this case, _implementation is a StateVariable which is inherited by the proxy,
            and this is accessed directly (without a contract call) when delegating. 
            Therefore it doesn't make sense to change self._delegate_variable to reference 
            whatever gets returned by registry.getVersion(_version) instead of _implementation.
            So, rather than check for a CallExpression here and trace it to its source if found,
            we leave that to be done later by the ProxyFeatureExtraction class, and simply
            update var_to_set here by giving assigning it an expression.
            """
            right = assignment.expression_right
            var_to_set.expression = right
        if setter is None and "facet" in str(var_to_set):
            """
            Handle the corner case for EIP-2535 Diamond proxy
            The function diamondCut is used to add/delete/modify logic contracts (it is the setter)
            But, this function is implemented in a facet (logic) contract itself, i.e. DiamondCutFacet
            This facet is added by the constructor, using LibDiamond.diamondCut, and subsequent calls
            to diamondCut are handled by the fallback(), which delegates to the DiamondCutFacet
            ex: /tests/proxies/DiamondFactory.sol
            """
            constructor = contract.constructors_declared
            if constructor is not None:
                for n in constructor.all_nodes():
                    if n.type == NodeType.EXPRESSION:
                        exp = n.expression
                        if isinstance(exp, CallExpression):
                            # TODO: Remove dependence on function name "diamondCut"
                            if "diamondCut" in str(exp.called):
                                diamond_cut = exp.arguments[0]
                                if isinstance(diamond_cut, Identifier) and "DiamondCut" in str(diamond_cut.value.type):
                                    idiamond_cut = contract.compilation_unit.get_contract_from_name("IDiamondCut")
                                    cut_facet = idiamond_cut
                                    for c in contract.compilation_unit.contracts:
                                        if c == idiamond_cut:
                                            continue
                                        if idiamond_cut in c.inheritance:
                                            cut_facet = c
                                    if cut_facet != idiamond_cut:
                                        """ Found implementation of DiamondCutFacet """
                                        for f in cut_facet.functions:
                                            if f.name == "diamondCut":
                                                setter = f
                                                break
                                    else:
                                        lib_diamond = contract.compilation_unit.get_contract_from_name("LibDiamond")
                                        setter = lib_diamond.get_function_from_name("diamondCut")
                                        if setter is not None:
                                            break
                        elif isinstance(exp, AssignmentOperation):
                            left = exp.expression_left
                            right = exp.expression_right
                            if isinstance(left, IndexAccess):
                                left = left.expression_left
                                if isinstance(left, Identifier) and str(left.value.type) == "bytes4[]":
                                    if isinstance(right, MemberAccess) and right.member_name == "selector":
                                        right = right.expression
                                        if isinstance(right, MemberAccess):
                                            member_name = right.member_name
                                            member_of = right.expression
                                            if isinstance(member_of, Identifier):
                                                value = member_of.value
                                                if isinstance(value, Contract):
                                                    setter = value.get_function_from_name(member_name)
                                                    break
        return setter, var_to_set

    def handle_local_delegate_from_call_exp(self) -> bool:
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.expressions.type_conversion import TypeConversion
        from slither.core.expressions.call_expression import CallExpression
        from slither.core.solidity_types.user_defined_type import UserDefinedType
        from slither.core.expressions.member_access import MemberAccess
        from slither.core.expressions.identifier import Identifier

        if isinstance(self._delegate_variable, LocalVariable):
            call = self._delegate_variable.expression
            if isinstance(call, CallExpression):
                call = call.called
                if isinstance(call, MemberAccess):
                    e = call.expression
                    if isinstance(e, CallExpression) and isinstance(e.called, Identifier):
                        f = e.called.value
                        if isinstance(f, Function):
                            ret_node = f.return_node()
                            if ret_node is not None:
                                e = f.return_node().expression
                            else:
                                ret_val = f.returns[0]
                                e = Identifier(ret_val)
                    if isinstance(e, TypeConversion) or isinstance(e, Identifier):
                        ctype = e.type
                        if isinstance(e, Identifier):
                            if isinstance(e.value, Contract):
                                ctype = UserDefinedType(e.value)
                            else:
                                ctype = e.value.type
                        if isinstance(ctype, UserDefinedType) and isinstance(ctype.type,
                                                                             Contract) and ctype.type != self:
                            contract = ctype.type
                            if contract.is_interface:
                                # call destination to retrieve delegate target is hidden in an interface,
                                # cannot use cross-contract analysis to confirm upgradeability
                                self._is_upgradeable_proxy = True
                                self._is_upgradeable_proxy_confirmed = False
        return self._is_upgradeable_proxy

    def handle_delegate_state_var_different_contract(self):
        # Whenever we call find_setter_in_contract, we should also update _delegate_variable, in case
        # find_setter_in_contract found an AssignmentOperation and updated _delegate_variable.expression
        (self._proxy_impl_setter,
         self._delegate_variable) = self.find_setter_in_contract(self._delegate_variable.contract,
                                                                 self._delegate_variable,
                                                                 self._proxy_impl_slot)
        if self._proxy_impl_setter is None:
            # Failed to find setter in self._delegate_variable.contract, so look in self
            (self._proxy_impl_setter,
             self._delegate_variable) = self.find_setter_in_contract(self, self._delegate_variable,
                                                                     self._proxy_impl_slot)
            if self._proxy_impl_setter is None:
                # Failed to find setter in self, so scan the rest of the compilation unit contracts
                for c in self.compilation_unit.contracts:
                    if c == self or c == self._delegate_variable.contract or self in c.inheritance:
                        continue
                    if self._proxy_impl_setter is not None:
                        break
                    if self._delegate_variable.contract in c.inheritance:
                        (self._proxy_impl_setter,
                         self._delegate_variable) = self.find_setter_in_contract(c, self._delegate_variable,
                                                                                 self._proxy_impl_slot)

    def handle_delegate_local_var_different_contract(self):
        (self._proxy_impl_setter,
         self._delegate_variable) = self.find_setter_in_contract(self._delegate_variable.function.contract,
                                                                 self._delegate_variable, self._proxy_impl_slot)
        if self._proxy_impl_setter is None:
            for c in self.compilation_unit.contracts:
                if c == self or c == self._delegate_variable.function.contract or self in c.inheritance:
                    continue
                if self._delegate_variable.function.contract in c.inheritance:
                    (self._proxy_impl_setter,
                     self._delegate_variable) = self.find_setter_in_contract(c, self._delegate_variable,
                                                                             self._proxy_impl_slot)

    def handle_missing_getter(self) -> bool:
        from slither.core.cfg.node import NodeType
        from slither.core.variables.state_variable import StateVariable
        from slither.core.variables.local_variable import LocalVariable
        from slither.core.variables.structure_variable import StructureVariable
        from slither.core.declarations.function_contract import FunctionContract

        delegate_contract = None
        if isinstance(self._delegate_variable, StateVariable) and self._delegate_variable.contract != self:
            delegate_contract = self._delegate_variable.contract
        elif isinstance(self._delegate_variable, LocalVariable) and \
                isinstance(self._delegate_variable.function, FunctionContract) and \
                self._delegate_variable.function.contract != self:
            delegate_contract = self._delegate_variable.function.contract
        elif isinstance(self._delegate_variable, StructureVariable) and \
                isinstance(self._delegate_variable.structure, StructureContract) and \
                self._delegate_variable.structure.contract != self:
            delegate_contract = self._delegate_variable.structure.contract
        if delegate_contract is not None:
            for c in self.compilation_unit.contracts:
                if delegate_contract in c.inheritance and c != self and self not in c.inheritance:
                    self._proxy_impl_getter = self.find_getter_in_contract(c, self._delegate_variable)
                    if self._proxy_impl_setter is None:
                        (self._proxy_impl_setter,
                         self._delegate_variable) = self.find_setter_in_contract(c, self._delegate_variable, None)
                    if self._proxy_impl_setter is not None:
                        self._is_upgradeable_proxy = True
                        self._is_upgradeable_proxy_confirmed = True
                        return self._is_upgradeable_proxy
                    elif self._proxy_impl_getter is not None:
                        self._is_upgradeable_proxy = self.getter_return_is_non_constant()
                        return self._is_upgradeable_proxy
        """
        Handle the case where the delegate address is a state variable which is also declared in the
        implementation contract at the same position in storage, in which case the setter may be
        located in the implementation contract, though we have no other clues that this may be the case.
        """
        if isinstance(self._delegate_variable, StateVariable):
            index = -1
            for idx, var in enumerate(self.state_variables_ordered):
                if var == self._delegate_variable:
                    index = idx
                    break
            if index >= 0:
                for c in self.compilation_unit.contracts:
                    if len(c.state_variables_ordered) < index + 1 or c == self:
                        continue
                    var = c.state_variables_ordered[index]
                    if var.name != self._delegate_variable.name and self._delegate_variable == self._proxy_impl_slot:
                        var = c.get_state_variable_from_name(self._delegate_variable.name)
                    if var is not None:
                        if var.name == self._delegate_variable.name and var.type == self._delegate_variable.type:
                            self._proxy_impl_getter = self.find_getter_in_contract(c, var)
                            if self._proxy_impl_setter is None:
                                (self._proxy_impl_setter,
                                 self._delegate_variable) = self.find_setter_in_contract(c, var, None)
                            if self._proxy_impl_setter is not None:
                                self._is_upgradeable_proxy = True
                                self._is_upgradeable_proxy_confirmed = True
                                return self._is_upgradeable_proxy
                            elif self._proxy_impl_getter is not None:
                                return c.getter_return_is_non_constant()
        """
        Handle the case, as in EIP 1822, where the Proxy has no implementation getter because it is
        loaded explicitly from a hard-coded slot within the fallback itself.
        We assume in this case that, if the Proxy needs to load the implementation address from storage slot
        then the address must not be constant - otherwise why not use a constant address
        This is only necessary if the Proxy also doesn't have an implementation setter, because it is
        located in another contract. The assumption is only necessary if we do not search cross-contracts.
        """
        if self._proxy_impl_slot is not None or self._delegate_variable.expression is not None:
            for c in self.compilation_unit.contracts:
                if c != self and self not in c.inheritance:
                    self._proxy_impl_getter = self.find_getter_in_contract(c, self._delegate_variable)
                    if self._proxy_impl_setter is None:
                        (self._proxy_impl_setter,
                         self._delegate_variable) = self.find_setter_in_contract(c, self._delegate_variable,
                                                                                 self._proxy_impl_slot)
                    if self._proxy_impl_setter is not None:
                        self._is_upgradeable_proxy = True
                        self._is_upgradeable_proxy_confirmed = True
                        return self._is_upgradeable_proxy
                    elif self._proxy_impl_getter is not None:
                        return c.getter_return_is_non_constant()
        else:
            for n in self.fallback_function.all_nodes():
                if n.type == NodeType.ASSEMBLY:
                    inline_asm = n.inline_asm
                    if inline_asm and "sload" in str(inline_asm):  # and self._delegates_to.name in inline_asm:
                        self._is_upgradeable_proxy = True
        return self._is_upgradeable_proxy

    @is_upgradeable_proxy.setter
    def is_upgradeable_proxy(self, upgradeable_proxy: bool) -> None:
        self._is_upgradeable_proxy = upgradeable_proxy

    @property
    def upgradeable_version(self) -> Optional[str]:
        return self._upgradeable_version

    @upgradeable_version.setter
    def upgradeable_version(self, version_name: str) -> None:
        self._upgradeable_version = version_name

    # endregion
    ###################################################################################
    ###################################################################################
    # region Internals
    ###################################################################################
    ###################################################################################

    @property
    def is_incorrectly_constructed(self) -> bool:
        """
        Return true if there was an internal Slither's issue when analyzing the contract
        :return:
        """
        return self._is_incorrectly_parsed

    @is_incorrectly_constructed.setter
    def is_incorrectly_constructed(self, incorrect: bool) -> None:
        self._is_incorrectly_parsed = incorrect

    def add_constructor_variables(self) -> None:
        from slither.core.declarations.function_contract import FunctionContract

        if self.state_variables:
            for (idx, variable_candidate) in enumerate(self.state_variables):
                if variable_candidate.expression and not variable_candidate.is_constant:

                    constructor_variable = FunctionContract(self.compilation_unit)
                    constructor_variable.set_function_type(FunctionType.CONSTRUCTOR_VARIABLES)
                    constructor_variable.set_contract(self)  # type: ignore
                    constructor_variable.set_contract_declarer(self)  # type: ignore
                    constructor_variable.set_visibility("internal")
                    # For now, source mapping of the constructor variable is the whole contract
                    # Could be improved with a targeted source mapping
                    constructor_variable.set_offset(self.source_mapping, self.compilation_unit)
                    self._functions[constructor_variable.canonical_name] = constructor_variable

                    prev_node = self._create_node(
                        constructor_variable, 0, variable_candidate, constructor_variable
                    )
                    variable_candidate.node_initialization = prev_node
                    counter = 1
                    for v in self.state_variables[idx + 1 :]:
                        if v.expression and not v.is_constant:
                            next_node = self._create_node(
                                constructor_variable, counter, v, prev_node.scope
                            )
                            v.node_initialization = next_node
                            prev_node.add_son(next_node)
                            next_node.add_father(prev_node)
                            prev_node = next_node
                            counter += 1
                    break

            for (idx, variable_candidate) in enumerate(self.state_variables):
                if variable_candidate.expression and variable_candidate.is_constant:

                    constructor_variable = FunctionContract(self.compilation_unit)
                    constructor_variable.set_function_type(
                        FunctionType.CONSTRUCTOR_CONSTANT_VARIABLES
                    )
                    constructor_variable.set_contract(self)  # type: ignore
                    constructor_variable.set_contract_declarer(self)  # type: ignore
                    constructor_variable.set_visibility("internal")
                    # For now, source mapping of the constructor variable is the whole contract
                    # Could be improved with a targeted source mapping
                    constructor_variable.set_offset(self.source_mapping, self.compilation_unit)
                    self._functions[constructor_variable.canonical_name] = constructor_variable

                    prev_node = self._create_node(
                        constructor_variable, 0, variable_candidate, constructor_variable
                    )
                    variable_candidate.node_initialization = prev_node
                    counter = 1
                    for v in self.state_variables[idx + 1 :]:
                        if v.expression and v.is_constant:
                            next_node = self._create_node(
                                constructor_variable, counter, v, prev_node.scope
                            )
                            v.node_initialization = next_node
                            prev_node.add_son(next_node)
                            next_node.add_father(prev_node)
                            prev_node = next_node
                            counter += 1

                    break

    def _create_node(
        self, func: Function, counter: int, variable: "Variable", scope: Union[Scope, Function]
    ) -> "Node":
        from slither.core.cfg.node import Node, NodeType
        from slither.core.expressions import (
            AssignmentOperationType,
            AssignmentOperation,
            Identifier,
        )

        # Function uses to create node for state variable declaration statements
        node = Node(NodeType.OTHER_ENTRYPOINT, counter, scope, func.file_scope)
        node.set_offset(variable.source_mapping, self.compilation_unit)
        node.set_function(func)
        func.add_node(node)
        assert variable.expression
        expression = AssignmentOperation(
            Identifier(variable),
            variable.expression,
            AssignmentOperationType.ASSIGN,
            variable.type,
        )

        expression.set_offset(variable.source_mapping, self.compilation_unit)
        node.add_expression(expression)
        return node

    # endregion
    ###################################################################################
    ###################################################################################
    # region SlithIR
    ###################################################################################
    ###################################################################################

    def convert_expression_to_slithir_ssa(self) -> None:
        """
        Assume generate_slithir_and_analyze was called on all functions

        :return:
        """
        from slither.slithir.variables import StateIRVariable

        all_ssa_state_variables_instances = {}

        for contract in self.inheritance:
            for v in contract.state_variables_declared:
                new_var = StateIRVariable(v)
                all_ssa_state_variables_instances[v.canonical_name] = new_var
                self._initial_state_variables.append(new_var)

        for v in self.variables:
            if v.contract == self:
                new_var = StateIRVariable(v)
                all_ssa_state_variables_instances[v.canonical_name] = new_var
                self._initial_state_variables.append(new_var)

        for func in self.functions + list(self.modifiers):
            func.generate_slithir_ssa(all_ssa_state_variables_instances)

    def fix_phi(self) -> None:
        last_state_variables_instances: Dict[str, List["StateVariable"]] = {}
        initial_state_variables_instances: Dict[str, "StateVariable"] = {}
        for v in self._initial_state_variables:
            last_state_variables_instances[v.canonical_name] = []
            initial_state_variables_instances[v.canonical_name] = v

        for func in self.functions + list(self.modifiers):
            result = func.get_last_ssa_state_variables_instances()
            for variable_name, instances in result.items():
                # TODO: investigate the next operation
                last_state_variables_instances[variable_name] += list(instances)

        for func in self.functions + list(self.modifiers):
            func.fix_phi(last_state_variables_instances, initial_state_variables_instances)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Built in definitions
    ###################################################################################
    ###################################################################################

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return other == self.name
        return NotImplemented

    def __neq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return other != self.name
        return NotImplemented

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return self._id  # type:ignore

    # endregion
