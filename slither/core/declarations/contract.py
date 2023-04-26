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

from slither.core.declarations.function import Function, FunctionType, FunctionLanguage
from slither.utils.erc import (
    ERC20_signatures,
    ERC165_signatures,
    ERC223_signatures,
    ERC721_signatures,
    ERC1820_signatures,
    ERC777_signatures,
    ERC1155_signatures,
    ERC2612_signatures,
    ERC1363_signatures,
    ERC4524_signatures,
    ERC4626_signatures,
)
from slither.utils.tests_pattern import is_test_contract

# pylint: disable=too-many-lines,too-many-instance-attributes,import-outside-toplevel,too-many-nested-blocks
if TYPE_CHECKING:
    from slither.utils.type_helpers import LibraryCallType, HighLevelCallType, InternalCallType
    from slither.core.declarations import (
        Enum,
        Event,
        Modifier,
        EnumContract,
        StructureContract,
        FunctionContract,
        CustomErrorContract,
    )
    from slither.slithir.variables.variable import SlithIRVariable
    from slither.core.variables import Variable, StateVariable
    from slither.core.compilation_unit import SlitherCompilationUnit
    from slither.core.scope.scope import FileScope
    from slither.core.cfg.node import Node


LOGGER = logging.getLogger("Contract")

USING_FOR_KEY = Union[str, Type]
USING_FOR_ITEM = List[Union[Type, Function]]


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
        self._events: Dict[str, "Event"] = {}
        # map accessible variable from name -> variable
        # do not contain private variables inherited from contract
        self._variables: Dict[str, "StateVariable"] = {}
        self._variables_ordered: List["StateVariable"] = []
        self._modifiers: Dict[str, "Modifier"] = {}
        self._functions: Dict[str, "FunctionContract"] = {}
        self._linearizedBaseContracts: List[int] = []
        self._custom_errors: Dict[str, "CustomErrorContract"] = {}

        # The only str is "*"
        self._using_for: Dict[USING_FOR_KEY, USING_FOR_ITEM] = {}
        self._using_for_complete: Optional[Dict[USING_FOR_KEY, USING_FOR_ITEM]] = None
        self._kind: Optional[str] = None
        self._is_interface: bool = False
        self._is_library: bool = False
        self._is_fully_implemented: bool = False

        self._signatures: Optional[List[str]] = None
        self._signatures_declared: Optional[List[str]] = None

        self._fallback_function: Optional["FunctionContract"] = None
        self._receive_function: Optional["FunctionContract"] = None

        self._is_upgradeable: Optional[bool] = None
        self._is_upgradeable_proxy: Optional[bool] = None
        self._upgradeable_version: Optional[str] = None

        self._initial_state_variables: List["StateVariable"] = []  # ssa

        self._is_incorrectly_parsed: bool = False

        self._available_functions_as_dict: Optional[Dict[str, "Function"]] = None
        self._all_functions_called: Optional[List["InternalCallType"]] = None

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
        assert self._id
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
        return self._is_fully_implemented

    @is_fully_implemented.setter
    def is_fully_implemented(self, is_fully_implemented: bool):
        self._is_fully_implemented = is_fully_implemented

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
    def events(self) -> List["Event"]:
        """
        list(Event): List of the events
        """
        return list(self._events.values())

    @property
    def events_inherited(self) -> List["Event"]:
        """
        list(Event): List of the inherited events
        """
        return [e for e in self.events if e.contract != self]

    @property
    def events_declared(self) -> List["Event"]:
        """
        list(Event): List of the events declared within the contract (not inherited)
        """
        return [e for e in self.events if e.contract == self]

    @property
    def events_as_dict(self) -> Dict[str, "Event"]:
        return self._events

    # endregion
    ###################################################################################
    ###################################################################################
    # region Using for
    ###################################################################################
    ###################################################################################

    @property
    def using_for(self) -> Dict[USING_FOR_KEY, USING_FOR_ITEM]:
        return self._using_for

    @property
    def using_for_complete(self) -> Dict[USING_FOR_KEY, USING_FOR_ITEM]:
        """
        Dict[Union[str, Type], List[Type]]: Dict of merged local using for directive with top level directive
        """

        def _merge_using_for(
            uf1: Dict[USING_FOR_KEY, USING_FOR_ITEM], uf2: Dict[USING_FOR_KEY, USING_FOR_ITEM]
        ) -> Dict[USING_FOR_KEY, USING_FOR_ITEM]:
            result = {**uf1, **uf2}
            for key, value in result.items():
                if key in uf1 and key in uf2:
                    result[key] = value + uf1[key]
            return result

        if self._using_for_complete is None:
            result = self.using_for
            top_level_using_for = self.file_scope.using_for_directives
            for uftl in top_level_using_for:
                result = _merge_using_for(result, uftl.using_for)
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
    # region Variables
    ###################################################################################
    ###################################################################################

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
        Use state_variables_ordered for all the variables following the storage order

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
        return list(self._variables_ordered)

    def add_variables_ordered(self, new_vars: List["StateVariable"]) -> None:
        self._variables_ordered += new_vars

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

    def get_function_from_canonical_name(self, canonical_name: str) -> Optional["Function"]:
        """
            Return a function from a a canonical name (contract.signature())
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
        return next((v for v in self.state_variables if v.name == canonical_name), None)

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
            Return the list of functions overriden by the function
        Args:
            (core.Function)
        Returns:
            list(core.Function)

        """
        candidatess = [c.functions_declared for c in self.inheritance]
        candidates = [candidate for sublist in candidatess for candidate in sublist]
        return [f for f in candidates if f.full_name == function.full_name]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Recursive getters
    ###################################################################################
    ###################################################################################

    @property
    def all_functions_called(self) -> List["InternalCallType"]:
        """
        list(Function): List of functions reachable from the contract
        Includes super, and private/internal functions not shadowed
        """
        if self._all_functions_called is None:
            all_functions = [f for f in self.functions + self.modifiers if not f.is_shadowed]  # type: ignore
            all_callss = [f.all_internal_calls() for f in all_functions] + [list(all_functions)]
            all_calls = [item for sublist in all_callss for item in sublist]
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
    def all_library_calls(self) -> List["LibraryCallType"]:
        """
        list((Contract, Function): List all of the libraries func called
        """
        all_high_level_callss = [f.all_library_calls() for f in self.functions + self.modifiers]  # type: ignore
        all_high_level_calls = [item for sublist in all_high_level_callss for item in sublist]
        return list(set(all_high_level_calls))

    @property
    def all_high_level_calls(self) -> List["HighLevelCallType"]:
        """
        list((Contract, Function|Variable)): List all of the external high level calls
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
        from slither.core.cfg.node import NodeType
        from slither.slithir.operations import LowLevelCall

        if self._is_upgradeable_proxy is None:
            self._is_upgradeable_proxy = False
            if "Proxy" in self.name:
                self._is_upgradeable_proxy = True
                return True
            for f in self.functions:
                if f.is_fallback:
                    for node in f.all_nodes():
                        for ir in node.irs:
                            if isinstance(ir, LowLevelCall) and ir.function_name == "delegatecall":
                                self._is_upgradeable_proxy = True
                                return self._is_upgradeable_proxy
                        if node.type == NodeType.ASSEMBLY:
                            inline_asm = node.inline_asm
                            if inline_asm:
                                if "delegatecall" in inline_asm:
                                    self._is_upgradeable_proxy = True
                                    return self._is_upgradeable_proxy
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
