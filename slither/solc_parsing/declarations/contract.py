import logging
from typing import List, Dict, Callable, TYPE_CHECKING, Union

from slither.core.declarations import Modifier, Structure, Event
from slither.core.declarations.contract import Contract
from slither.core.declarations.enum import Enum
from slither.core.declarations.function import Function
from slither.core.variables.state_variable import StateVariable
from slither.solc_parsing.declarations.event import EventSolc
from slither.solc_parsing.declarations.function import FunctionSolc
from slither.solc_parsing.declarations.modifier import ModifierSolc
from slither.solc_parsing.declarations.structure import StructureSolc
from slither.solc_parsing.exceptions import ParsingError, VariableNotFound
from slither.solc_parsing.solidity_types.type_parsing import parse_type
from slither.solc_parsing.types.types import ContractDefinition, FunctionDefinition, EventDefinition, \
    InheritanceSpecifier, VariableDeclaration, EnumDefinition, ModifierDefinition, StructDefinition, UsingForDirective
from slither.solc_parsing.variables.state_variable import StateVariableSolc

LOGGER = logging.getLogger("ContractSolcParsing")

if TYPE_CHECKING:
    from slither.solc_parsing.slitherSolc import SlitherSolc
    from slither.core.slither_core import SlitherCore

# pylint: disable=too-many-instance-attributes,import-outside-toplevel,too-many-nested-blocks,too-many-public-methods


class ContractSolc:
    def __init__(self, slither_parser: "SlitherSolc", contract: Contract, data: ContractDefinition):
        self._contract = contract
        self._contract.set_slither(slither_parser.core)
        self._slither_parser = slither_parser
        self._data = data

        self._functionsNotParsed: List[FunctionDefinition] = []
        self._modifiersNotParsed: List[ModifierDefinition] = []
        self._functions_no_params: List[FunctionSolc] = []
        self._modifiers_no_params: List[ModifierSolc] = []
        self._eventsNotParsed: List[EventDefinition] = []
        self._variablesNotParsed: List[VariableDeclaration] = []
        self._enumsNotParsed: List[EnumDefinition] = []
        self._structuresNotParsed: List[StructDefinition] = []
        self._usingForNotParsed: List[UsingForDirective] = []

        self._functions_parser: List[FunctionSolc] = []
        self._modifiers_parser: List[ModifierSolc] = []
        self._structures_parser: List[StructureSolc] = []

        self._is_analyzed: bool = False

        # use to remap inheritance id
        self._remapping: Dict[str, str] = {}

        self.baseContracts = []
        self.baseConstructorContractsCalled = []
        self._linearized_base_contracts: List[int]

        self._variables_parser: List[StateVariableSolc] = []

        # Export info
        self._contract.id = self._data.id
        self._contract.name = self._data.name

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

    def set_is_analyzed(self, is_analyzed: bool):
        self._is_analyzed = is_analyzed

    @property
    def underlying_contract(self) -> Contract:
        return self._contract

    @property
    def linearized_base_contracts(self) -> List[int]:
        return self._linearized_base_contracts

    @property
    def slither(self) -> "SlitherCore":
        return self._contract.slither

    @property
    def slither_parser(self) -> "SlitherSolc":
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
        if self._data.kind:
            if self._data.kind == "interface":
                self._contract.is_interface = True
            self._contract.kind = self._data.kind

        self._linearized_base_contracts = self._data.linearized_base_contracts

        # Parse base contract information
        self._parse_base_contract_info()

        # trufle does some re-mapping of id
        for base_contract in self._data.base_contracts:
            if not base_contract.basename.referenced_declaration:
                continue

            self._remapping[str(base_contract.basename.referenced_declaration)] = base_contract.basename.name

    def _parse_base_contract_info(self):
        for base_contract in self._data.base_contracts:
            referenced_declaration = base_contract.basename.referenced_declaration
            if not referenced_declaration:
                continue

            self.baseContracts.append(referenced_declaration)

            if base_contract.args is not None:
                self.baseConstructorContractsCalled.append(referenced_declaration)

    def _parse_contract_items(self):
        for node in self._data.nodes:
            if isinstance(node, FunctionDefinition):
                self._functionsNotParsed.append(node)
            elif isinstance(node, EventDefinition):
                self._eventsNotParsed.append(node)
            elif isinstance(node, InheritanceSpecifier):
                # we dont need to parse it as it is redundant
                # with self.linearizedBaseContracts
                continue
            elif isinstance(node, VariableDeclaration):
                self._variablesNotParsed.append(node)
            elif isinstance(node, EnumDefinition):
                self._enumsNotParsed.append(node)
            elif isinstance(node, ModifierDefinition):
                self._modifiersNotParsed.append(node)
            elif isinstance(node, StructDefinition):
                self._structuresNotParsed.append(node)
            elif isinstance(node, UsingForDirective):
                self._usingForNotParsed.append(node)
            else:
                raise ParsingError("Unknown contract item: ", node.__class__)
        return

    def _parse_struct(self, struct: StructDefinition):
        name = struct.name
        if struct.canonical_name:
            canonical_name = struct.canonical_name
        else:
            canonical_name = self._contract.name + "." + name

        st = Structure()
        st.set_contract(self._contract)
        st.set_offset(struct.src, self._contract.slither)

        st_parser = StructureSolc(st, name, canonical_name, struct.members, self)
        self._contract.structures_as_dict[name] = st
        self._structures_parser.append(st_parser)

    def parse_structs(self):
        for father in self._contract.inheritance_reverse:
            self._contract.structures_as_dict.update(father.structures_as_dict)

        for struct in self._structuresNotParsed:
            self._parse_struct(struct)
        self._structuresNotParsed.clear()

    def parse_state_variables(self):
        for father in self._contract.inheritance_reverse:
            self._contract.variables_as_dict.update(father.variables_as_dict)
            self._contract.add_variables_ordered(
                [
                    var
                    for var in father.state_variables_ordered
                    if var not in self._contract.state_variables_ordered
                ]
            )

        for varNotParsed in self._variablesNotParsed:
            var = StateVariable()
            var.set_offset(varNotParsed.src, self._contract.slither)
            var.set_contract(self._contract)

            var_parser = StateVariableSolc(var, varNotParsed)
            self._variables_parser.append(var_parser)

            self._contract.variables_as_dict[var.name] = var
            self._contract.add_variables_ordered([var])

    def _parse_modifier(self, modifier_data: ModifierDefinition):
        modif = Modifier()
        modif.set_offset(modifier_data.src, self._contract.slither)
        modif.set_contract(self._contract)
        modif.set_contract_declarer(self._contract)

        modif_parser = ModifierSolc(modif, modifier_data, self)
        self._contract.slither.add_modifier(modif)
        self._modifiers_no_params.append(modif_parser)
        self._modifiers_parser.append(modif_parser)

        self._slither_parser.add_functions_parser(modif_parser)

    def parse_modifiers(self):
        for modifier in self._modifiersNotParsed:
            self._parse_modifier(modifier)
        self._modifiersNotParsed.clear()

    def _parse_function(self, function_data: FunctionDefinition):
        func = Function()
        func.set_offset(function_data.src, self._contract.slither)
        func.set_contract(self._contract)
        func.set_contract_declarer(self._contract)

        func_parser = FunctionSolc(func, function_data, self)
        self._contract.slither.add_function(func)
        self._functions_no_params.append(func_parser)
        self._functions_parser.append(func_parser)

        self._slither_parser.add_functions_parser(func_parser)

    def parse_functions(self):

        for function in self._functionsNotParsed:
            self._parse_function(function)

        self._functionsNotParsed.clear()

    # endregion
    ###################################################################################
    ###################################################################################
    # region Analyze
    ###################################################################################
    ###################################################################################

    def log_incorrect_parsing(self, error):
        if self._contract.slither.disallow_partial:
            raise ParsingError(error)
        LOGGER.error(error)
        self._contract.is_incorrectly_parsed = True

    def analyze_content_modifiers(self):
        try:
            for modifier_parser in self._modifiers_parser:
                modifier_parser.analyze_content()
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing modifier {e}")

    def analyze_content_functions(self):
        try:
            for function_parser in self._functions_parser:
                function_parser.analyze_content()
        except (VariableNotFound, KeyError, ParsingError) as e:
            self.log_incorrect_parsing(f"Missing function {e}")

    def analyze_params_modifiers(self):
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
        self._modifiers_no_params.clear()

    def analyze_params_functions(self):
        try:
            elements_no_params = self._functions_no_params
            getter = lambda c: c.functions_parser
            getter_available = lambda c: c.functions_declared
            Cls = Function
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
        self._functions_no_params.clear()

    def _analyze_params_elements(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        elements_no_params: List[FunctionSolc],
        getter: Callable[["ContractSolc"], List[FunctionSolc]],
        getter_available: Callable[[Contract], List[Function]],
        Cls: Callable,
        Cls_parser: Callable,
        parser: List[FunctionSolc],
    ) -> Dict[str, Union[Function, Modifier]]:
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

        try:
            for father in self._contract.inheritance:
                father_parser = self._slither_parser.underlying_contract_to_parser[father]
                for element_parser in getter(father_parser):
                    elem = Cls()
                    elem.set_contract(self._contract)
                    elem.set_contract_declarer(element_parser.underlying_function.contract_declarer)
                    elem.set_offset(
                        element_parser.function_not_parsed.src, self._contract.slither
                    )

                    elem_parser = Cls_parser(
                        elem,
                        element_parser.function_not_parsed,
                        self,
                    )
                    elem_parser.analyze_params()
                    if isinstance(elem, Modifier):
                        self._contract.slither.add_modifier(elem)
                    else:
                        self._contract.slither.add_function(elem)

                    self._slither_parser.add_functions_parser(elem_parser)

                    all_elements[elem.canonical_name] = elem
                    parser.append(elem_parser)

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

    def analyze_constant_state_variables(self):
        for var_parser in self._variables_parser:
            if var_parser.underlying_variable.is_constant:
                # cant parse constant expression based on function calls
                try:
                    var_parser.analyze(self)
                except (VariableNotFound, KeyError) as e:
                    LOGGER.error(e)

    def analyze_state_variables(self):
        try:
            for var_parser in self._variables_parser:
                var_parser.analyze(self)
            return
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing state variable {e}")

    def analyze_using_for(self):
        try:
            for father in self._contract.inheritance:
                self._contract.using_for.update(father.using_for)

            for item in self._usingForNotParsed:
                lib_name = parse_type(item.library, self)
                if item.typename:
                    type_name = parse_type(item.typename, self)
                else:
                    type_name = "*"

                if type_name not in self._contract.using_for:
                    self._contract.using_for[type_name] = []
                self._contract.using_for[type_name].append(lib_name)
            self._usingForNotParsed.clear()
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing using for {e}")

    def analyze_enums(self):
        try:
            for father in self._contract.inheritance:
                self._contract.enums_as_dict.update(father.enums_as_dict)

            for enum in self._enumsNotParsed:
                # for enum, we can parse and analyze it
                # at the same time
                self._analyze_enum(enum)
            self._enumsNotParsed.clear()
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

        new_enum = Enum(name, canonical_name, values)
        new_enum.set_contract(self._contract)
        new_enum.set_offset(enum.src, self._contract.slither)
        self._contract.enums_as_dict[canonical_name] = new_enum

    def _analyze_struct(self, struct: StructureSolc):  # pylint: disable=no-self-use
        struct.analyze()

    def analyze_structs(self):
        try:
            for struct in self._structures_parser:
                self._analyze_struct(struct)
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing struct {e}")

    def analyze_events(self):
        try:
            for father in self._contract.inheritance_reverse:
                self._contract.events_as_dict.update(father.events_as_dict)

            for event_to_parse in self._eventsNotParsed:
                event = Event()
                event.set_contract(self._contract)
                event.set_offset(event_to_parse.src, self._contract.slither)

                event_parser = EventSolc(event, event_to_parse, self)
                event_parser.analyze(self)
                self._contract.events_as_dict[event.full_name] = event
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing event {e}")

        self._eventsNotParsed.clear()

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
        self._functionsNotParsed.clear()
        self._modifiersNotParsed.clear()
        self._functions_no_params.clear()
        self._modifiers_no_params.clear()
        self._eventsNotParsed.clear()
        self._variablesNotParsed.clear()
        self._enumsNotParsed.clear()
        self._structuresNotParsed.clear()
        self._usingForNotParsed.clear()

    # endregion
    ###################################################################################
    ###################################################################################
    # region Built in definitions
    ###################################################################################
    ###################################################################################

    def __hash__(self):
        return self._contract.id

    # endregion
