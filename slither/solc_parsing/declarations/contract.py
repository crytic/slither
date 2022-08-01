import logging
from typing import List, Dict, Callable, TYPE_CHECKING, Union, Set

from slither.core.declarations import Modifier, Event, EnumContract, StructureContract, Function
from slither.core.declarations.contract import Contract
from slither.core.declarations.custom_error_contract import CustomErrorContract
from slither.core.declarations.function_contract import FunctionContract
from slither.core.solidity_types import ElementaryType, TypeAliasContract
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

LOGGER = logging.getLogger("ContractSolcParsing")

if TYPE_CHECKING:
    from slither.solc_parsing.slither_compilation_unit_solc import SlitherCompilationUnitSolc
    from slither.core.slither_core import SlitherCore
    from slither.core.compilation_unit import SlitherCompilationUnit

# pylint: disable=too-many-instance-attributes,import-outside-toplevel,too-many-nested-blocks,too-many-public-methods


class ContractSolc(CallerContextExpression):
    def __init__(self, slither_parser: "SlitherCompilationUnitSolc", contract: Contract, data):
        # assert slitherSolc.solc_version.startswith('0.4')

        self._contract = contract
        self._slither_parser = slither_parser
        self._data = data

        self._functionsNotParsed: List[Dict] = []
        self._modifiersNotParsed: List[Dict] = []
        self._functions_no_params: List[FunctionSolc] = []
        self._modifiers_no_params: List[ModifierSolc] = []
        self._eventsNotParsed: List[Dict] = []
        self._variablesNotParsed: List[Dict] = []
        self._enumsNotParsed: List[Dict] = []
        self._structuresNotParsed: List[Dict] = []
        self._usingForNotParsed: List[Dict] = []
        self._customErrorParsed: List[Dict] = []

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

        # Export info
        if self.is_compact_ast:
            self._contract.name = self._data["name"]
        else:
            self._contract.name = self._data["attributes"][self.get_key()]

        self._contract.id = self._data["id"]

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

    ###################################################################################
    ###################################################################################
    # region AST
    ###################################################################################
    ###################################################################################

    def get_key(self) -> str:
        return self._slither_parser.get_key()

    def get_children(self, key="nodes") -> str:
        if self.is_compact_ast:
            return key
        return "children"

    @property
    def remapping(self) -> Dict[str, str]:
        return self._remapping

    @property
    def is_compact_ast(self) -> bool:
        return self._slither_parser.is_compact_ast

    # endregion
    ###################################################################################
    ###################################################################################
    # region SlithIR
    ###################################################################################
    ###################################################################################

    def _parse_contract_info(self):
        if self.is_compact_ast:
            attributes = self._data
        else:
            attributes = self._data["attributes"]

        self._contract.is_interface = False
        if "contractKind" in attributes:
            if attributes["contractKind"] == "interface":
                self._contract.is_interface = True
            elif attributes["contractKind"] == "library":
                self._contract.is_library = True
            self._contract.contract_kind = attributes["contractKind"]

        self._linearized_base_contracts = attributes["linearizedBaseContracts"]
        # self._contract.fullyImplemented = attributes["fullyImplemented"]

        # Parse base contract information
        self._parse_base_contract_info()

        # trufle does some re-mapping of id
        if "baseContracts" in self._data:
            for elem in self._data["baseContracts"]:
                if elem["nodeType"] == "InheritanceSpecifier":
                    self._remapping[elem["baseName"]["referencedDeclaration"]] = elem["baseName"][
                        "name"
                    ]

    def _parse_base_contract_info(self):  # pylint: disable=too-many-branches
        # Parse base contracts (immediate, non-linearized)
        if self.is_compact_ast:
            # Parse base contracts + constructors in compact-ast
            if "baseContracts" in self._data:
                for base_contract in self._data["baseContracts"]:
                    if base_contract["nodeType"] != "InheritanceSpecifier":
                        continue
                    if (
                        "baseName" not in base_contract
                        or "referencedDeclaration" not in base_contract["baseName"]
                    ):
                        continue

                    # Obtain our contract reference and add it to our base contract list
                    referencedDeclaration = base_contract["baseName"]["referencedDeclaration"]
                    self.baseContracts.append(referencedDeclaration)

                    # If we have defined arguments in our arguments object, this is a constructor invocation.
                    # (note: 'arguments' can be [], which is not the same as None. [] implies a constructor was
                    #  called with no arguments, while None implies no constructor was called).
                    if "arguments" in base_contract and base_contract["arguments"] is not None:
                        self.baseConstructorContractsCalled.append(referencedDeclaration)
        else:
            # Parse base contracts + constructors in legacy-ast
            if "children" in self._data:
                for base_contract in self._data["children"]:
                    if base_contract["name"] != "InheritanceSpecifier":
                        continue
                    if "children" not in base_contract or len(base_contract["children"]) == 0:
                        continue
                    # Obtain all items for this base contract specification (base contract, followed by arguments)
                    base_contract_items = base_contract["children"]
                    if (
                        "name" not in base_contract_items[0]
                        or base_contract_items[0]["name"] != "UserDefinedTypeName"
                    ):
                        continue
                    if (
                        "attributes" not in base_contract_items[0]
                        or "referencedDeclaration" not in base_contract_items[0]["attributes"]
                    ):
                        continue

                    # Obtain our contract reference and add it to our base contract list
                    referencedDeclaration = base_contract_items[0]["attributes"][
                        "referencedDeclaration"
                    ]
                    self.baseContracts.append(referencedDeclaration)

                    # If we have an 'attributes'->'arguments' which is None, this is not a constructor call.
                    if (
                        "attributes" not in base_contract
                        or "arguments" not in base_contract["attributes"]
                        or base_contract["attributes"]["arguments"] is not None
                    ):
                        self.baseConstructorContractsCalled.append(referencedDeclaration)

    def _parse_contract_items(self):
        # pylint: disable=too-many-branches
        if not self.get_children() in self._data:  # empty contract
            return
        for item in self._data[self.get_children()]:
            if item[self.get_key()] == "FunctionDefinition":
                self._functionsNotParsed.append(item)
            elif item[self.get_key()] == "EventDefinition":
                self._eventsNotParsed.append(item)
            elif item[self.get_key()] == "InheritanceSpecifier":
                # we dont need to parse it as it is redundant
                # with self.linearizedBaseContracts
                continue
            elif item[self.get_key()] == "VariableDeclaration":
                self._variablesNotParsed.append(item)
            elif item[self.get_key()] == "EnumDefinition":
                self._enumsNotParsed.append(item)
            elif item[self.get_key()] == "ModifierDefinition":
                self._modifiersNotParsed.append(item)
            elif item[self.get_key()] == "StructDefinition":
                self._structuresNotParsed.append(item)
            elif item[self.get_key()] == "UsingForDirective":
                self._usingForNotParsed.append(item)
            elif item[self.get_key()] == "ErrorDefinition":
                self._customErrorParsed.append(item)
            elif item[self.get_key()] == "UserDefinedValueTypeDefinition":
                self._parse_type_alias(item)
            else:
                raise ParsingError("Unknown contract item: " + item[self.get_key()])
        return

    def _parse_type_alias(self, item: Dict) -> None:
        assert "name" in item
        assert "underlyingType" in item
        underlying_type = item["underlyingType"]
        assert "nodeType" in underlying_type and underlying_type["nodeType"] == "ElementaryTypeName"
        assert "name" in underlying_type

        original_type = ElementaryType(underlying_type["name"])

        # For user defined types defined at the contract level the lookup can be done
        # Using the name or the canonical name
        # For example during the type parsing the canonical name
        # Note that Solidity allows shadowing of user defined types
        # Between top level and contract definitions
        alias = item["name"]
        alias_canonical = self._contract.name + "." + item["name"]

        user_defined_type = TypeAliasContract(original_type, alias, self.underlying_contract)
        user_defined_type.set_offset(item["src"], self.compilation_unit)
        self._contract.file_scope.user_defined_types[alias] = user_defined_type
        self._contract.file_scope.user_defined_types[alias_canonical] = user_defined_type

    def _parse_struct(self, struct: Dict):

        st = StructureContract(self._contract.compilation_unit)
        st.set_contract(self._contract)
        st.set_offset(struct["src"], self._contract.compilation_unit)

        st_parser = StructureContractSolc(st, struct, self)
        self._contract.structures_as_dict[st.name] = st
        self._structures_parser.append(st_parser)

    def parse_structs(self):
        for father in self._contract.inheritance_reverse:
            self._contract.structures_as_dict.update(father.structures_as_dict)

        for struct in self._structuresNotParsed:
            self._parse_struct(struct)
        self._structuresNotParsed = None

    def _parse_custom_error(self, custom_error: Dict):
        ce = CustomErrorContract(self.compilation_unit)
        ce.set_contract(self._contract)
        ce.set_offset(custom_error["src"], self.compilation_unit)

        ce_parser = CustomErrorSolc(ce, custom_error, self._slither_parser)
        self._contract.custom_errors_as_dict[ce.name] = ce
        self._custom_errors_parser.append(ce_parser)

    def parse_custom_errors(self):
        for father in self._contract.inheritance_reverse:
            self._contract.custom_errors_as_dict.update(father.custom_errors_as_dict)

        for custom_error in self._customErrorParsed:
            self._parse_custom_error(custom_error)
        self._customErrorParsed = None

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
            var.set_offset(varNotParsed["src"], self._contract.compilation_unit)
            var.set_contract(self._contract)

            var_parser = StateVariableSolc(var, varNotParsed)
            self._variables_parser.append(var_parser)

            self._contract.variables_as_dict[var.name] = var
            self._contract.add_variables_ordered([var])

    def _parse_modifier(self, modifier_data: Dict):
        modif = Modifier(self._contract.compilation_unit)
        modif.set_offset(modifier_data["src"], self._contract.compilation_unit)
        modif.set_contract(self._contract)
        modif.set_contract_declarer(self._contract)

        modif_parser = ModifierSolc(modif, modifier_data, self, self.slither_parser)
        self._contract.compilation_unit.add_modifier(modif)
        self._modifiers_no_params.append(modif_parser)
        self._modifiers_parser.append(modif_parser)

        self._slither_parser.add_function_or_modifier_parser(modif_parser)

    def parse_modifiers(self):
        for modifier in self._modifiersNotParsed:
            self._parse_modifier(modifier)
        self._modifiersNotParsed = None

    def _parse_function(self, function_data: Dict):
        func = FunctionContract(self._contract.compilation_unit)
        func.set_offset(function_data["src"], self._contract.compilation_unit)
        func.set_contract(self._contract)
        func.set_contract_declarer(self._contract)

        func_parser = FunctionSolc(func, function_data, self, self._slither_parser)
        self._contract.compilation_unit.add_function(func)
        self._functions_no_params.append(func_parser)
        self._functions_parser.append(func_parser)

        self._slither_parser.add_function_or_modifier_parser(func_parser)

    def parse_functions(self):

        for function in self._functionsNotParsed:
            self._parse_function(function)

        self._functionsNotParsed = None

    # endregion
    ###################################################################################
    ###################################################################################
    # region Analyze
    ###################################################################################
    ###################################################################################

    def log_incorrect_parsing(self, error):
        if self._contract.compilation_unit.core.disallow_partial:
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
        self._modifiers_no_params = []

    def analyze_params_functions(self):
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
    ):
        elem = Cls(self._contract.compilation_unit)
        elem.set_contract(self._contract)
        underlying_function = element_parser.underlying_function
        # TopLevel function are not analyzed here
        assert isinstance(underlying_function, FunctionContract)
        elem.set_contract_declarer(underlying_function.contract_declarer)
        elem.set_offset(
            element_parser.function_not_parsed["src"],
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

            if self.is_compact_ast:
                for using_for in self._usingForNotParsed:
                    lib_name = parse_type(using_for["libraryName"], self)
                    if "typeName" in using_for and using_for["typeName"]:
                        type_name = parse_type(using_for["typeName"], self)
                    else:
                        type_name = "*"
                    if type_name not in self._contract.using_for:
                        self._contract.using_for[type_name] = []
                    self._contract.using_for[type_name].append(lib_name)
            else:
                for using_for in self._usingForNotParsed:
                    children = using_for[self.get_children()]
                    assert children and len(children) <= 2
                    if len(children) == 2:
                        new = parse_type(children[0], self)
                        old = parse_type(children[1], self)
                    else:
                        new = parse_type(children[0], self)
                        old = "*"
                    if old not in self._contract.using_for:
                        self._contract.using_for[old] = []
                    self._contract.using_for[old].append(new)
            self._usingForNotParsed = []
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
            self._enumsNotParsed = None
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing enum {e}")

    def _analyze_enum(self, enum):
        # Enum can be parsed in one pass
        if self.is_compact_ast:
            name = enum["name"]
            canonicalName = enum["canonicalName"]
        else:
            name = enum["attributes"][self.get_key()]
            if "canonicalName" in enum["attributes"]:
                canonicalName = enum["attributes"]["canonicalName"]
            else:
                canonicalName = self._contract.name + "." + name
        values = []
        for child in enum[self.get_children("members")]:
            assert child[self.get_key()] == "EnumValue"
            if self.is_compact_ast:
                values.append(child["name"])
            else:
                values.append(child["attributes"][self.get_key()])

        new_enum = EnumContract(name, canonicalName, values)
        new_enum.set_contract(self._contract)
        new_enum.set_offset(enum["src"], self._contract.compilation_unit)
        self._contract.enums_as_dict[canonicalName] = new_enum

    def _analyze_struct(self, struct: StructureContractSolc):  # pylint: disable=no-self-use
        struct.analyze()

    def analyze_structs(self):
        try:
            for struct in self._structures_parser:
                self._analyze_struct(struct)
        except (VariableNotFound, KeyError) as e:
            self.log_incorrect_parsing(f"Missing struct {e}")

    def analyze_custom_errors(self):
        for custom_error in self._custom_errors_parser:
            custom_error.analyze_params()

    def analyze_events(self):
        try:
            for father in self._contract.inheritance_reverse:
                self._contract.events_as_dict.update(father.events_as_dict)

            for event_to_parse in self._eventsNotParsed:
                event = Event()
                event.set_contract(self._contract)
                event.set_offset(event_to_parse["src"], self._contract.compilation_unit)

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

    # endregion
    ###################################################################################
    ###################################################################################
    # region Built in definitions
    ###################################################################################
    ###################################################################################

    def __hash__(self):
        return self._contract.id

    # endregion
