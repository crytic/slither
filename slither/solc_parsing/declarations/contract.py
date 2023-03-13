import logging
import re
from typing import Any, List, Dict, Callable, TYPE_CHECKING, Union, Set

from slither.core.declarations import Modifier, Event, EnumContract, StructureContract, Function
from slither.core.declarations.contract import Contract
from slither.core.declarations.custom_error_contract import CustomErrorContract
from slither.core.declarations.function_contract import FunctionContract
from slither.core.solidity_types import ElementaryType, TypeAliasContract, Type
from slither.core.variables.state_variable import StateVariable
from slither.solc_parsing.declarations.caller_context import CallerContextExpression
from slither.solc_parsing.declarations.custom_error import CustomErrorSolc
from slither.solc_parsing.declarations.event import EventSolc
from slither.solc_parsing.declarations.function import FunctionSolc
from slither.solc_parsing.declarations.modifier import ModifierSolc
from slither.solc_parsing.declarations.structure_contract import StructureContractSolc
from slither.solc_parsing.exceptions import ParsingError, VariableNotFound
from slither.solc_parsing.solidity_types.type_parsing import parse_type
from slither.solc_parsing.variables.state_variable import StateVariableSolc
from slither.solc_parsing.ast.types import (
    ContractDefinition,
    EventDefinition,
    UsingForDirective,
    StructDefinition,
    EnumDefinition,
    VariableDeclaration,
    FunctionDefinition,
    ErrorDefinition,
    ModifierDefinition,
    UserDefinedValueTypeDefinition,
    InheritanceSpecifier,
    WildCardTypeName,
)

LOGGER = logging.getLogger("ContractSolcParsing")

if TYPE_CHECKING:
    from slither.solc_parsing.slither_compilation_unit_solc import SlitherCompilationUnitSolc
    from slither.core.compilation_unit import SlitherCompilationUnit

# pylint: disable=too-many-instance-attributes,import-outside-toplevel,too-many-nested-blocks,too-many-public-methods


class ContractSolc(CallerContextExpression):
    def __init__(
        self,
        slither_parser: "SlitherCompilationUnitSolc",
        contract: Contract,
        contract_def: ContractDefinition,
    ):
        # assert slitherSolc.solc_version.startswith('0.4')

        self._contract = contract
        self._slither_parser = slither_parser
        self._contract_def = contract_def

        self._functionsNotParsed: List[FunctionDefinition] = []
        self._modifiersNotParsed: List[ModifierDefinition] = []
        self._functions_no_params: List[FunctionSolc] = []
        self._modifiers_no_params: List[ModifierSolc] = []
        self._eventsNotParsed: List[EventDefinition] = []
        self._variablesNotParsed: List[VariableDeclaration] = []
        self._enumsNotParsed: List[EnumDefinition] = []
        self._structuresNotParsed: List[StructDefinition] = []
        self._usingForNotParsed: List[UsingForDirective] = []
        self._customErrorParsed: List[ErrorDefinition] = []

        self._functions_parser: List[FunctionSolc] = []
        self._modifiers_parser: List[ModifierSolc] = []
        self._structures_parser: List[StructureContractSolc] = []
        self._custom_errors_parser: List[CustomErrorSolc] = []

        self._is_analyzed: bool = False

        # use to remap inheritance id
        self._remapping: Dict[str, str] = {}

        self.baseContracts: List[str] = []
        self.baseConstructorContractsCalled: List[str] = []
        self._linearized_base_contracts: List[int]

        self._variables_parser: List[StateVariableSolc] = []

        self._contract.name = self._contract_def.name
        self._contract.id = self._contract_def.id

        self._handle_comment()
        self._parse_contract_info()
        self._parse_contract_items()

    ###################################################################################
    ###################################################################################
    # region General Properties
    ###################################################################################
    ###################################################################################

    @property
    def is_analyzed(self) -> bool:
        return self._is_analyzed

    def set_is_analyzed(self, is_analyzed: bool) -> None:
        self._is_analyzed = is_analyzed

    @property
    def underlying_contract(self) -> Contract:
        return self._contract

    @property
    def linearized_base_contracts(self) -> List[int]:
        return self._linearized_base_contracts

    @property
    def compilation_unit(self) -> "SlitherCompilationUnit":
        return self._contract.compilation_unit

    @property
    def slither_parser(self) -> "SlitherCompilationUnitSolc":
        return self._slither_parser

    @property
    def functions_parser(self) -> List["FunctionSolc"]:
        return self._functions_parser

    @property
    def modifiers_parser(self) -> List["ModifierSolc"]:
        return self._modifiers_parser

    @property
    def structures_not_parsed(self) -> List[Dict]:
        return self._structuresNotParsed

    @property
    def enums_not_parsed(self) -> List[Dict]:
        return self._enumsNotParsed

    # endregion
    ###################################################################################
    ###################################################################################
    # region AST
    ###################################################################################
    ###################################################################################

    @property
    def remapping(self) -> Dict[str, str]:
        return self._remapping

    # endregion
    ###################################################################################
    ###################################################################################
    # region SlithIR
    ###################################################################################
    ###################################################################################

    def _parse_contract_info(self):
        self._contract.is_interface = False
        if self._contract_def.kind:
            if self._contract_def.kind == "interface":
                self._contract.is_interface = True
            elif self._contract_def.kind == "library":
                self._contract.is_library = True
            self._contract.contract_kind = self._contract_def.kind

        self._linearized_base_contracts = self._contract_def.linearized_base_contracts

        # Parse base contract information
        self._parse_base_contract_info()

        # trufle does some re-mapping of id
        for base_contract in self._contract_def.base_contracts:
            if not base_contract.basename.referenced_declaration:
                continue

            self._remapping[
                str(base_contract.basename.referenced_declaration)
            ] = base_contract.basename.name

    def _parse_base_contract_info(self):
        for base_contract in self._contract_def.base_contracts:
            referenced_declaration = base_contract.basename.referenced_declaration
            if not referenced_declaration:
                continue

            self.baseContracts.append(referenced_declaration)

            if base_contract.args is not None:
                self.baseConstructorContractsCalled.append(referenced_declaration)

    def _parse_contract_items(self):
        for child in self._contract_def.nodes:
            if isinstance(child, FunctionDefinition):
                self._functionsNotParsed.append(child)
            elif isinstance(child, EventDefinition):
                self._eventsNotParsed.append(child)
            elif isinstance(child, InheritanceSpecifier):
                # we dont need to parse it as it is redundant
                # with self.linearizedBaseContracts
                continue
            elif isinstance(child, VariableDeclaration):
                self._variablesNotParsed.append(child)
            elif isinstance(child, EnumDefinition):
                self._enumsNotParsed.append(child)
            elif isinstance(child, ModifierDefinition):
                self._modifiersNotParsed.append(child)
            elif isinstance(child, StructDefinition):
                self._structuresNotParsed.append(child)
            elif isinstance(child, UsingForDirective):
                self._usingForNotParsed.append(child)
            elif isinstance(child, ErrorDefinition):
                self._customErrorParsed.append(child)
            elif isinstance(child, UserDefinedValueTypeDefinition):
                self._parse_type_alias(child)
            else:
                raise ParsingError("Unknown contract item: " + child)

    def _parse_type_alias(self, item: UserDefinedValueTypeDefinition) -> None:
        # For user defined types defined at the contract level the lookup
        # can be done using the name or the canonical name.
        # For example during the type parsing the canonical name
        # Note, that Solidity allows shadowing of user defined types
        # between top level and contract definitions.
        alias = item.name
        alias_canonical = self._contract.name + "." + alias

        user_defined_type = TypeAliasContract(
            ElementaryType(item.underlying_type.name), alias, self.underlying_contract
        )
        user_defined_type.set_offset(item.src, self.compilation_unit)
        self._contract.file_scope.user_defined_types[alias] = user_defined_type
        self._contract.file_scope.user_defined_types[alias_canonical] = user_defined_type

    def _parse_struct(self, struct: StructDefinition):

        st = StructureContract(self._contract.compilation_unit)
        st.set_contract(self._contract)
        st.set_offset(struct.src, self._contract.compilation_unit)

        st_parser = StructureContractSolc(st, struct, self)
        self._contract.structures_as_dict[st.name] = st
        self._structures_parser.append(st_parser)

    def parse_structs(self) -> None:
        for father in self._contract.inheritance_reverse:
            self._contract.structures_as_dict.update(father.structures_as_dict)

        for struct in self._structuresNotParsed:
            self._parse_struct(struct)
        self._structuresNotParsed = None

    def _parse_custom_error(self, custom_error: ErrorDefinition):
        ce = CustomErrorContract(self.compilation_unit)
        ce.set_contract(self._contract)
        ce.set_offset(custom_error.src, self.compilation_unit)

        ce_parser = CustomErrorSolc(ce, custom_error, self._slither_parser)
        self._contract.custom_errors_as_dict[ce.name] = ce
        self._custom_errors_parser.append(ce_parser)

    def parse_custom_errors(self) -> None:
        for father in self._contract.inheritance_reverse:
            self._contract.custom_errors_as_dict.update(father.custom_errors_as_dict)

        for custom_error in self._customErrorParsed:
            self._parse_custom_error(custom_error)
        self._customErrorParsed = None

    def parse_state_variables(self) -> None:
        for father in self._contract.inheritance_reverse:
            self._contract.variables_as_dict.update(
                {
                    name: v
                    for name, v in father.variables_as_dict.items()
                    if v.visibility != "private"
                }
            )
            self._contract.add_variables_ordered(
                [
                    var
                    for var in father.state_variables_ordered
                    if var not in self._contract.state_variables_ordered
                ]
            )

        for varNotParsed in self._variablesNotParsed:
            var = StateVariable()
            var.set_offset(varNotParsed.src, self._contract.compilation_unit)
            var.set_contract(self._contract)

            var_parser = StateVariableSolc(var, varNotParsed)
            self._variables_parser.append(var_parser)

            self._contract.variables_as_dict[var.name] = var
            self._contract.add_variables_ordered([var])

    def _parse_modifier(self, modifier_data: ModifierDefinition):
        modif = Modifier(self._contract.compilation_unit)
        modif.set_offset(modifier_data.src, self._contract.compilation_unit)
        modif.set_contract(self._contract)
        modif.set_contract_declarer(self._contract)

        modif_parser = ModifierSolc(modif, modifier_data, self, self.slither_parser)
        self._contract.compilation_unit.add_modifier(modif)
        self._modifiers_no_params.append(modif_parser)
        self._modifiers_parser.append(modif_parser)

        self._slither_parser.add_function_or_modifier_parser(modif_parser)

    def parse_modifiers(self) -> None:
        for modifier in self._modifiersNotParsed:
            self._parse_modifier(modifier)
        self._modifiersNotParsed = None

    def _parse_function(self, function_def: FunctionDefinition):
        func = FunctionContract(self._contract.compilation_unit)
        func.set_offset(function_def.src, self._contract.compilation_unit)
        func.set_contract(self._contract)
        func.set_contract_declarer(self._contract)

        func_parser = FunctionSolc(func, function_def, self, self._slither_parser)
        self._contract.compilation_unit.add_function(func)
        self._functions_no_params.append(func_parser)
        self._functions_parser.append(func_parser)

        self._slither_parser.add_function_or_modifier_parser(func_parser)

    def parse_functions(self) -> None:

        for function in self._functionsNotParsed:
            self._parse_function(function)

        self._functionsNotParsed = None

    # endregion
    ###################################################################################
    ###################################################################################
    # region Analyze
    ###################################################################################
    ###################################################################################

    def log_incorrect_parsing(self, error: str) -> None:
        if self._contract.compilation_unit.core.disallow_partial:
            raise ParsingError(error)
        LOGGER.error(error)
        self._contract.is_incorrectly_constructed = True

    def analyze_content_modifiers(self) -> None:
        try:
            for modifier_parser in self._modifiers_parser:
                modifier_parser.analyze_content()
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing modifier {e}")

    def analyze_content_functions(self) -> None:
        try:
            for function_parser in self._functions_parser:
                function_parser.analyze_content()
        except VariableNotFound as e:
            self.log_incorrect_parsing(e)
        except (KeyError, ParsingError) as e:
            self.log_incorrect_parsing(f"Missing function {e}")

    def analyze_params_modifiers(self) -> None:
        try:
            elements_no_params = self._modifiers_no_params
            getter = lambda c: c.modifiers_parser
            getter_available = lambda c: c.modifiers_declared
            Cls = Modifier
            Cls_parser = ModifierSolc
            modifiers = self._analyze_params_elements(
                elements_no_params,
                getter,
                getter_available,
                Cls,
                Cls_parser,
                self._modifiers_parser,
            )
            self._contract.set_modifiers(modifiers)
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing params {e}")
        self._modifiers_no_params = []

    def analyze_params_functions(self) -> None:
        try:
            elements_no_params = self._functions_no_params
            getter = lambda c: c.functions_parser
            getter_available = lambda c: c.functions_declared
            Cls = FunctionContract
            Cls_parser = FunctionSolc
            functions = self._analyze_params_elements(
                elements_no_params,
                getter,
                getter_available,
                Cls,
                Cls_parser,
                self._functions_parser,
            )
            self._contract.set_functions(functions)
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing params {e}")
        self._functions_no_params = []

    def _analyze_params_element(  # pylint: disable=too-many-arguments
        self,
        Cls: Callable,
        Cls_parser: Callable,
        element_parser: FunctionSolc,
        explored_reference_id: Set[str],
        parser: List[FunctionSolc],
        all_elements: Dict[str, Function],
    ) -> None:
        elem = Cls(self._contract.compilation_unit)
        elem.set_contract(self._contract)
        underlying_function = element_parser.underlying_function
        # TopLevel function are not analyzed here
        assert isinstance(underlying_function, FunctionContract)
        elem.set_contract_declarer(underlying_function.contract_declarer)
        elem.set_offset(
            element_parser.function_not_parsed.src,
            self._contract.compilation_unit,
        )

        elem_parser = Cls_parser(
            elem, element_parser.function_not_parsed, self, self.slither_parser
        )
        if (
            element_parser.underlying_function.id
            and element_parser.underlying_function.id in explored_reference_id
        ):
            # Already added from other fathers
            return
        if element_parser.underlying_function.id:
            explored_reference_id.add(element_parser.underlying_function.id)
        elem_parser.analyze_params()
        if isinstance(elem, Modifier):
            self._contract.compilation_unit.add_modifier(elem)
        else:
            self._contract.compilation_unit.add_function(elem)

        self._slither_parser.add_function_or_modifier_parser(elem_parser)

        all_elements[elem.canonical_name] = elem
        parser.append(elem_parser)

    def _analyze_params_elements(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        elements_no_params: List[FunctionSolc],
        getter: Callable[["ContractSolc"], List[FunctionSolc]],
        getter_available: Callable[[Contract], List[FunctionContract]],
        Cls: Callable,
        Cls_parser: Callable,
        parser: List[FunctionSolc],
    ) -> Dict[str, Union[FunctionContract, Modifier]]:
        """
        Analyze the parameters of the given elements (Function or Modifier).
        The function iterates over the inheritance to create an instance or inherited elements (Function or Modifier)
        If the element is shadowed, set is_shadowed to True

        :param elements_no_params: list of elements to analyzer
        :param getter: fun x
        :param getter_available: fun x
        :param Cls: Class to create for collision
        :return:
        """
        all_elements = {}

        explored_reference_id = set()
        try:
            for father in self._contract.inheritance:
                father_parser = self._slither_parser.underlying_contract_to_parser[father]
                for element_parser in getter(father_parser):
                    self._analyze_params_element(
                        Cls, Cls_parser, element_parser, explored_reference_id, parser, all_elements
                    )

            accessible_elements = self._contract.available_elements_from_inheritances(
                all_elements, getter_available
            )

            # If there is a constructor in the functions
            # We remove the previous constructor
            # As only one constructor is present per contracts
            #
            # Note: contract.all_functions_called returns the constructors of the base contracts
            has_constructor = False
            for element_parser in elements_no_params:
                element_parser.analyze_params()
                if element_parser.underlying_function.is_constructor:
                    has_constructor = True

            if has_constructor:
                _accessible_functions = {
                    k: v for (k, v) in accessible_elements.items() if not v.is_constructor
                }

            for element_parser in elements_no_params:
                accessible_elements[
                    element_parser.underlying_function.full_name
                ] = element_parser.underlying_function
                all_elements[
                    element_parser.underlying_function.canonical_name
                ] = element_parser.underlying_function

            for element in all_elements.values():
                if accessible_elements[element.full_name] != all_elements[element.canonical_name]:
                    element.is_shadowed = True
                    accessible_elements[element.full_name].shadows = True
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing params {e}")
        return all_elements

    def analyze_constant_state_variables(self) -> None:
        for var_parser in self._variables_parser:
            if var_parser.underlying_variable.is_constant:
                # cant parse constant expression based on function calls
                try:
                    var_parser.analyze(self)
                except (VariableNotFound, KeyError) as e:
                    LOGGER.error(e)

    def analyze_state_variables(self) -> None:
        try:
            for var_parser in self._variables_parser:
                var_parser.analyze(self)
            return
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing state variable {e}")

    def analyze_using_for(self) -> None:  # pylint: disable=too-many-branches
        try:
            for father in self._contract.inheritance:
                self._contract.using_for.update(father.using_for)

            for using_for in self._usingForNotParsed:
                if isinstance(using_for.typename, WildCardTypeName):
                    type_name = "*"
                else:
                    assert using_for.typename
                    type_name = parse_type(using_for.typename, self)
                if type_name not in self._contract.using_for:
                    self._contract.using_for[type_name] = []

                if using_for.library:
                    self._contract.using_for[type_name].append(parse_type(using_for.library, self))
                else:
                    # We have a list of functions. A function can be topLevel or a library function
                    self._analyze_function_list(using_for.function_list, type_name)

            self._usingForNotParsed.clear()

        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing using for {e}")

    def _analyze_function_list(self, function_list: List, type_name: Type) -> None:
        for f in function_list:
            full_name_split = f.name.split(".")
            if len(full_name_split) == 1:
                # Top level function
                function_name = full_name_split[0]
                self._analyze_top_level_function(function_name, type_name)
            elif len(full_name_split) == 2:
                # It can be a top level function behind an aliased import
                # or a library function
                first_part = full_name_split[0]
                function_name = full_name_split[1]
                self._check_aliased_import(first_part, function_name, type_name)
            else:
                # MyImport.MyLib.a we don't care of the alias
                library_name = full_name_split[1]
                function_name = full_name_split[2]
                self._analyze_library_function(library_name, function_name, type_name)

    def _check_aliased_import(self, first_part: str, function_name: str, type_name: Type) -> None:
        # We check if the first part appear as alias for an import
        # if it is then function_name must be a top level function
        # otherwise it's a library function
        for i in self._contract.file_scope.imports:
            if i.alias == first_part:
                self._analyze_top_level_function(function_name, type_name)
                return
        self._analyze_library_function(first_part, function_name, type_name)

    def _analyze_top_level_function(self, function_name: str, type_name: Type) -> None:
        for tl_function in self.compilation_unit.functions_top_level:
            if tl_function.name == function_name:
                self._contract.using_for[type_name].append(tl_function)

    def _analyze_library_function(
        self, library_name: str, function_name: str, type_name: Type
    ) -> None:
        # Get the library function
        found = False
        for c in self.compilation_unit.contracts:
            if found:
                break
            if c.name == library_name:
                for f in c.functions:
                    if f.name == function_name:
                        self._contract.using_for[type_name].append(f)
                        found = True
                        break
        if not found:
            self.log_incorrect_parsing(
                f"Contract level using for: Library {library_name} - function {function_name} not found"
            )

    def analyze_enums(self) -> None:
        try:
            for father in self._contract.inheritance:
                self._contract.enums_as_dict.update(father.enums_as_dict)

            for enum in self._enumsNotParsed:
                # for enum, we can parse and analyze it
                # at the same time
                self._analyze_enum(enum)
            self._enumsNotParsed = None
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing enum {e}")

    def _analyze_enum(self, enum: EnumDefinition):
        # Enum can be parsed in one pass
        name = enum.name
        if enum.canonical_name:
            canonical_name = enum.canonical_name
        else:
            canonical_name = self._contract.name + "." + enum.name
        values = []
        for child in enum.members:
            values.append(child.name)

        new_enum = EnumContract(name, canonical_name, values)
        new_enum.set_contract(self._contract)
        new_enum.set_offset(enum.src, self._contract.compilation_unit)
        self._contract.enums_as_dict[canonical_name] = new_enum

    def _analyze_struct(self, struct: StructureContractSolc) -> None:  # pylint: disable=no-self-use
        struct.analyze()

    def analyze_structs(self) -> None:
        try:
            for struct in self._structures_parser:
                self._analyze_struct(struct)
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing struct {e}")

    def analyze_custom_errors(self) -> None:
        for custom_error in self._custom_errors_parser:
            custom_error.analyze_params()

    def analyze_events(self) -> None:
        try:
            for father in self._contract.inheritance_reverse:
                self._contract.events_as_dict.update(father.events_as_dict)

            for event_to_parse in self._eventsNotParsed:
                event = Event()
                event.set_contract(self._contract)
                event.set_offset(event_to_parse.src, self._contract.compilation_unit)

                event_parser = EventSolc(event, event_to_parse, self)
                event_parser.analyze(self)
                self._contract.events_as_dict[event.full_name] = event
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing event {e}")

        self._eventsNotParsed = None

    # endregion
    ###################################################################################
    ###################################################################################
    # region Internal
    ###################################################################################
    ###################################################################################

    def delete_content(self):
        """
        Remove everything not parsed from the contract
        This is used only if something went wrong with the inheritance parsing
        :return:
        """
        self._functionsNotParsed = []
        self._modifiersNotParsed = []
        self._functions_no_params = []
        self._modifiers_no_params = []
        self._eventsNotParsed = []
        self._variablesNotParsed = []
        self._enumsNotParsed = []
        self._structuresNotParsed = []
        self._usingForNotParsed = []
        self._customErrorParsed = []

    def _handle_comment(self) -> None:
        if self._contract_def.documentation:
            candidates = self._contract_def.documentation.replace("\n", ",").split(",")

            for candidate in candidates:
                if "@custom:security isDelegatecallProxy" in candidate:
                    self._contract.is_upgradeable_proxy = True
                if "@custom:security isUpgradeable" in candidate:
                    self._contract.is_upgradeable = True

                version_name = re.search(r"@custom:version name=([\w-]+)", candidate)
                if version_name:
                    self._contract.upgradeable_version = version_name.group(1)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Built in definitions
    ###################################################################################
    ###################################################################################

    def __hash__(self):
        return self._contract.id

    # endregion
