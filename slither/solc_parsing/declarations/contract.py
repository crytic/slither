import logging

from slither.core.declarations.contract import Contract
from slither.core.declarations.enum import Enum
from slither.slithir.variables import StateIRVariable
from slither.solc_parsing.declarations.event import EventSolc
from slither.solc_parsing.declarations.function import FunctionSolc
from slither.solc_parsing.declarations.modifier import ModifierSolc
from slither.solc_parsing.declarations.structure import StructureSolc
from slither.solc_parsing.solidity_types.type_parsing import parse_type
from slither.solc_parsing.variables.state_variable import StateVariableSolc
from slither.solc_parsing.exceptions import ParsingError

logger = logging.getLogger("ContractSolcParsing")

class ContractSolc04(Contract):


    def __init__(self, slitherSolc, data):
        assert slitherSolc.solc_version.startswith('0.4')
        super(ContractSolc04, self).__init__()

        self.set_slither(slitherSolc)
        self._data = data

        self._functionsNotParsed = []
        self._modifiersNotParsed = []
        self._functions_no_params = []
        self._modifiers_no_params = []
        self._eventsNotParsed = []
        self._variablesNotParsed = []
        self._enumsNotParsed = []
        self._structuresNotParsed = []
        self._usingForNotParsed = []

        self._is_analyzed = False

        # use to remap inheritance id
        self._remapping = {}

        # Export info
        if self.is_compact_ast:
            self._name = self._data['name']
        else:
            self._name = self._data['attributes'][self.get_key()]

        self._id = self._data['id']

        self._inheritance = []

        self._parse_contract_info()
        self._parse_contract_items()


    ###################################################################################
    ###################################################################################
    # region General Properties
    ###################################################################################
    ###################################################################################

    @property
    def is_analyzed(self):
        return self._is_analyzed

    def set_is_analyzed(self, is_analyzed):
        self._is_analyzed = is_analyzed

    ###################################################################################
    ###################################################################################
    # region AST
    ###################################################################################
    ###################################################################################

    def get_key(self):
        return self.slither.get_key()

    def get_children(self, key='nodes'):
        if self.is_compact_ast:
            return key
        return 'children'

    @property
    def remapping(self):
        return self._remapping

    @property
    def is_compact_ast(self):
        return self.slither.is_compact_ast

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
            attributes = self._data['attributes']

        self.isInterface = False
        if 'contractKind' in attributes:
            if attributes['contractKind'] == 'interface':
                self.isInterface = True
            self._kind = attributes['contractKind']
        self.linearizedBaseContracts = attributes['linearizedBaseContracts']
        self.fullyImplemented = attributes['fullyImplemented']

        # Parse base contract information
        self._parse_base_contract_info()

        # trufle does some re-mapping of id
        if 'baseContracts' in self._data:
            for elem in self._data['baseContracts']:
                if elem['nodeType'] == 'InheritanceSpecifier':
                    self._remapping[elem['baseName']['referencedDeclaration']] = elem['baseName']['name']

    def _parse_base_contract_info(self):
        # Parse base contracts (immediate, non-linearized)
        self.baseContracts = []
        self.baseConstructorContractsCalled = []
        if self.is_compact_ast:
            # Parse base contracts + constructors in compact-ast
            if 'baseContracts' in self._data:
                for base_contract in self._data['baseContracts']:
                    if base_contract['nodeType'] != 'InheritanceSpecifier':
                        continue
                    if 'baseName' not in base_contract or 'referencedDeclaration' not in base_contract['baseName']:
                        continue

                    # Obtain our contract reference and add it to our base contract list
                    referencedDeclaration = base_contract['baseName']['referencedDeclaration']
                    self.baseContracts.append(referencedDeclaration)

                    # If we have defined arguments in our arguments object, this is a constructor invocation.
                    # (note: 'arguments' can be [], which is not the same as None. [] implies a constructor was
                    #  called with no arguments, while None implies no constructor was called).
                    if 'arguments' in base_contract and base_contract['arguments'] is not None:
                        self.baseConstructorContractsCalled.append(referencedDeclaration)
        else:
            # Parse base contracts + constructors in legacy-ast
            if 'children' in self._data:
                for base_contract in self._data['children']:
                    if base_contract['name'] != 'InheritanceSpecifier':
                        continue
                    if 'children' not in base_contract or len(base_contract['children']) == 0:
                        continue
                    # Obtain all items for this base contract specification (base contract, followed by arguments)
                    base_contract_items = base_contract['children']
                    if 'name' not in base_contract_items[0] or base_contract_items[0]['name'] != 'UserDefinedTypeName':
                        continue
                    if 'attributes' not in base_contract_items[0] or 'referencedDeclaration' not in \
                            base_contract_items[0]['attributes']:
                        continue

                    # Obtain our contract reference and add it to our base contract list
                    referencedDeclaration = base_contract_items[0]['attributes']['referencedDeclaration']
                    self.baseContracts.append(referencedDeclaration)

                    # If we have an 'attributes'->'arguments' which is None, this is not a constructor call.
                    if 'attributes' not in base_contract or 'arguments' not in base_contract['attributes'] or \
                            base_contract['attributes']['arguments'] is not None:
                        self.baseConstructorContractsCalled.append(referencedDeclaration)

    def _parse_contract_items(self):
        if not self.get_children() in self._data: # empty contract
            return
        for item in self._data[self.get_children()]:
            if item[self.get_key()] == 'FunctionDefinition':
                self._functionsNotParsed.append(item)
            elif item[self.get_key()] == 'EventDefinition':
                self._eventsNotParsed.append(item)
            elif item[self.get_key()] == 'InheritanceSpecifier':
                # we dont need to parse it as it is redundant
                # with self.linearizedBaseContracts
                continue
            elif item[self.get_key()] == 'VariableDeclaration':
                self._variablesNotParsed.append(item)
            elif item[self.get_key()] == 'EnumDefinition':
                self._enumsNotParsed.append(item)
            elif item[self.get_key()] == 'ModifierDefinition':
                self._modifiersNotParsed.append(item)
            elif item[self.get_key()] == 'StructDefinition':
                self._structuresNotParsed.append(item)
            elif item[self.get_key()] == 'UsingForDirective':
                self._usingForNotParsed.append(item)
            else:
                raise ParsingError('Unknown contract item: '+item[self.get_key()])
        return

    def _parse_struct(self, struct):
        if self.is_compact_ast:
            name = struct['name']
            attributes = struct
        else:
            name = struct['attributes'][self.get_key()]
            attributes = struct['attributes']
        if 'canonicalName' in attributes:
            canonicalName = attributes['canonicalName']
        else:
            canonicalName = self.name + '.' + name

        if self.get_children('members') in struct:
            children = struct[self.get_children('members')]
        else:
            children = [] # empty struct
        st = StructureSolc(name, canonicalName, children)
        st.set_contract(self)
        st.set_offset(struct['src'], self.slither)
        self._structures[name] = st

    def parse_structs(self):
        for father in self.inheritance_reverse:
            self._structures.update(father.structures_as_dict())

        for struct in self._structuresNotParsed:
            self._parse_struct(struct)
        self._structuresNotParsed = None

    def parse_state_variables(self):
        for father in self.inheritance_reverse:
            self._variables.update(father.variables_as_dict())

        for varNotParsed in self._variablesNotParsed:
            var = StateVariableSolc(varNotParsed)
            var.set_offset(varNotParsed['src'], self.slither)
            var.set_contract(self)

            self._variables[var.name] = var

    def _parse_modifier(self, modifier):

        modif = ModifierSolc(modifier, self, self)
        modif.set_contract(self)
        modif.set_contract_declarer(self)
        modif.set_offset(modifier['src'], self.slither)
        self.slither.add_modifier(modif)
        self._modifiers_no_params.append(modif)

    def parse_modifiers(self):

        for modifier in self._modifiersNotParsed:
            self._parse_modifier(modifier)
        self._modifiersNotParsed = None

        return

    def _parse_function(self, function):
        func = FunctionSolc(function, self, self)
        func.set_offset(function['src'], self.slither)
        self.slither.add_function(func)
        self._functions_no_params.append(func)

    def parse_functions(self):

        for function in self._functionsNotParsed:
            self._parse_function(function)


        self._functionsNotParsed = None

        return

    # endregion
    ###################################################################################
    ###################################################################################
    # region Analyze
    ###################################################################################
    ###################################################################################

    def analyze_content_modifiers(self):
        for modifier in self.modifiers:
            modifier.analyze_content()
        return

    def analyze_content_functions(self):
        for function in self.functions:
            function.analyze_content()

        return

    def analyze_params_modifiers(self):

        elements_no_params = self._modifiers_no_params
        getter = lambda f: f.modifiers
        getter_available = lambda f: f.available_modifiers_as_dict().items()
        Cls = ModifierSolc
        self._modifiers = self._analyze_params_elements(elements_no_params, getter, getter_available, Cls)

        self._modifiers_no_params = []

        return

    def analyze_params_functions(self):

        elements_no_params = self._functions_no_params
        getter = lambda f: f.functions
        getter_available = lambda f: f.available_functions_as_dict().items()
        Cls = FunctionSolc
        self._functions = self._analyze_params_elements(elements_no_params, getter, getter_available, Cls)

        self._functions_no_params = []
        return


    def _analyze_params_elements(self, elements_no_params, getter, getter_available, Cls):
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
        accessible_elements = {}

        for father in self.inheritance:
            for element in getter(father):
                elem = Cls(element._functionNotParsed, self, element.contract_declarer)
                elem.set_offset(element._functionNotParsed['src'], self.slither)
                elem.analyze_params()
                self.slither.add_function(elem)
                all_elements[elem.canonical_name] = elem

        accessible_elements = self.available_elements_from_inheritances(all_elements, getter_available)

        # If there is a constructor in the functions
        # We remove the previous constructor
        # As only one constructor is present per contracts
        #
        # Note: contract.all_functions_called returns the constructors of the base contracts
        has_constructor = False
        for element in elements_no_params:
            element.analyze_params()
            if element.is_constructor:
                has_constructor = True

        if has_constructor:
            _accessible_functions = {k: v for (k, v) in accessible_elements.items() if not v.is_constructor}

        for element in elements_no_params:
            accessible_elements[element.full_name] = element
            all_elements[element.canonical_name] = element

        for element in all_elements.values():
            if accessible_elements[element.full_name] != all_elements[element.canonical_name]:
                element.is_shadowed = True

        return all_elements



    def analyze_constant_state_variables(self):
        from slither.solc_parsing.expressions.expression_parsing import VariableNotFound
        for var in self.variables:
            if var.is_constant:
                # cant parse constant expression based on function calls
                try:
                    var.analyze(self)
                except VariableNotFound:
                    pass
        return

    def analyze_state_variables(self):
        for var in self.variables:
            var.analyze(self)
        return

    def analyze_using_for(self):
        for father in self.inheritance:
            self._using_for.update(father.using_for)

        if self.is_compact_ast:
            for using_for in self._usingForNotParsed:
                lib_name = parse_type(using_for['libraryName'], self)
                if 'typeName' in using_for and using_for['typeName']:
                    type_name = parse_type(using_for['typeName'], self)
                else:
                    type_name = '*'
                if not type_name in self._using_for:
                    self.using_for[type_name] = []
                self._using_for[type_name].append(lib_name)
        else:
            for using_for in self._usingForNotParsed:
                children = using_for[self.get_children()]
                assert children and len(children) <= 2
                if len(children) == 2:
                    new = parse_type(children[0], self)
                    old = parse_type(children[1], self)
                else:
                    new = parse_type(children[0], self)
                    old = '*'
                if not old in self._using_for:
                    self.using_for[old] = []
                self._using_for[old].append(new)
        self._usingForNotParsed = []

    def analyze_enums(self):

        for father in self.inheritance:
            self._enums.update(father.enums_as_dict())

        for enum in self._enumsNotParsed:
            # for enum, we can parse and analyze it 
            # at the same time
            self._analyze_enum(enum)
        self._enumsNotParsed = None

    def _analyze_enum(self, enum):
        # Enum can be parsed in one pass
        if self.is_compact_ast:
            name = enum['name']
            canonicalName = enum['canonicalName']
        else:
            name = enum['attributes'][self.get_key()]
            if 'canonicalName' in enum['attributes']:
                canonicalName = enum['attributes']['canonicalName']
            else:
                canonicalName = self.name + '.' + name
        values = []
        for child in enum[self.get_children('members')]:
            assert child[self.get_key()] == 'EnumValue'
            if self.is_compact_ast:
                values.append(child['name'])
            else:
                values.append(child['attributes'][self.get_key()])

        new_enum = Enum(name, canonicalName, values)
        new_enum.set_contract(self)
        new_enum.set_offset(enum['src'], self.slither)
        self._enums[canonicalName] = new_enum

    def _analyze_struct(self, struct):
        struct.analyze()

    def analyze_structs(self):
        for struct in self.structures:
            self._analyze_struct(struct)

    def analyze_events(self):
        for father in self.inheritance_reverse:
            self._events.update(father.events_as_dict())

        for event_to_parse in self._eventsNotParsed:
            event = EventSolc(event_to_parse, self)
            event.analyze(self)
            event.set_contract(self)
            event.set_offset(event_to_parse['src'], self.slither)
            self._events[event.full_name] = event

        self._eventsNotParsed = None



    # endregion
    ###################################################################################
    ###################################################################################
    # region SlithIR
    ###################################################################################
    ###################################################################################

    def convert_expression_to_slithir(self):
        for func in self.functions + self.modifiers:
            func.generate_slithir_and_analyze()

        all_ssa_state_variables_instances = dict()

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

        for func in self.functions + self.modifiers:
            func.generate_slithir_ssa(all_ssa_state_variables_instances)

    def fix_phi(self):
        last_state_variables_instances = dict()
        initial_state_variables_instances = dict()
        for v in self._initial_state_variables:
            last_state_variables_instances[v.canonical_name] = []
            initial_state_variables_instances[v.canonical_name] = v

        for func in self.functions + self.modifiers:
            result = func.get_last_ssa_state_variables_instances()
            for variable_name, instances in result.items():
                last_state_variables_instances[variable_name] += instances

        for func in self.functions + self.modifiers:
            func.fix_phi(last_state_variables_instances, initial_state_variables_instances)


    # endregion
    ###################################################################################
    ###################################################################################
    # region Built in definitions
    ###################################################################################
    ###################################################################################

    def __hash__(self):
        return self._id

    # endregion
