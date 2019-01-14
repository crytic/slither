import logging

from slither.core.declarations.contract import Contract
from slither.core.declarations.enum import Enum

from slither.solc_parsing.declarations.structure import StructureSolc
from slither.solc_parsing.declarations.event import EventSolc
from slither.solc_parsing.declarations.modifier import ModifierSolc
from slither.solc_parsing.declarations.function import FunctionSolc

from slither.solc_parsing.variables.state_variable import StateVariableSolc
from slither.solc_parsing.solidity_types.type_parsing import parse_type

from slither.slithir.variables import StateIRVariable

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


    @property
    def is_analyzed(self):
        return self._is_analyzed

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

    def set_is_analyzed(self, is_analyzed):
        self._is_analyzed = is_analyzed

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

        # Parse base contracts (immediate, non-linearized)
        self.baseContracts = []
        if self.is_compact_ast:
            if 'baseContracts' in attributes:
                for base_contract in attributes['baseContracts']:
                    if base_contract['nodeType'] == 'InheritanceSpecifier':
                        if 'baseName' in base_contract and 'referencedDeclaration' in base_contract['baseName']:
                            self.baseContracts.append(base_contract['baseName']['referencedDeclaration'])
        else:
            # TODO: Parse from legacy-ast. 'baseContracts' is unreliable here. Possibly use 'children'.
            pass

        # trufle does some re-mapping of id
        if 'baseContracts' in self._data:
            for elem in self._data['baseContracts']:
                if elem['nodeType'] == 'InheritanceSpecifier':
                    self._remapping[elem['baseName']['referencedDeclaration']] = elem['baseName']['name']

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
                logger.error('Unknown contract item: '+item[self.get_key()])
                exit(-1)
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

    def _analyze_struct(self, struct):
        struct.analyze()

    def parse_structs(self):
        for father in self.inheritance_reverse:
            self._structures.update(father.structures_as_dict())

        for struct in self._structuresNotParsed:
            self._parse_struct(struct)
        self._structuresNotParsed = None

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

    def parse_state_variables(self):
        for father in self.inheritance_reverse:
            self._variables.update(father.variables_as_dict())

        for varNotParsed in self._variablesNotParsed:
            var = StateVariableSolc(varNotParsed)
            var.set_offset(varNotParsed['src'], self.slither)
            var.set_contract(self)

            self._variables[var.name] = var

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

    def _parse_modifier(self, modifier):

        modif = ModifierSolc(modifier, self)
        modif.set_contract(self)
        modif.set_offset(modifier['src'], self.slither)
        self._modifiers_no_params.append(modif)

    def parse_modifiers(self):

        for modifier in self._modifiersNotParsed:
            self._parse_modifier(modifier)
        self._modifiersNotParsed = None

        return

    def _parse_function(self, function):
        func = FunctionSolc(function, self)
        func.set_offset(function['src'], self.slither)
        self._functions_no_params.append(func)

    def parse_functions(self):

        for function in self._functionsNotParsed:
            self._parse_function(function)


        self._functionsNotParsed = None

        return

    def analyze_params_modifiers(self):
        for father in self.inheritance_reverse:
            self._modifiers.update(father.modifiers_as_dict())

        for modifier in self._modifiers_no_params:
            modifier.analyze_params()
            self._modifiers[modifier.full_name] = modifier

        self._modifiers_no_params = []
        return

    def analyze_params_functions(self):
        # keep track of the contracts visited
        # to prevent an ovveride due to multiple inheritance of the same contract
        # A is B, C, D is C, --> the second C was already seen
        contracts_visited = []
        for father in self.inheritance_reverse:
            functions = {k:v for (k, v) in father.functions_as_dict().items()
                         if not v.contract in contracts_visited}
            contracts_visited.append(father)
            self._functions.update(functions)

        # If there is a constructor in the functions
        # We remove the previous constructor
        # As only one constructor is present per contracts
        #
        # Note: contract.all_functions_called returns the constructors of the base contracts
        has_constructor = False
        for function in self._functions_no_params:
            function.analyze_params()
            if function.is_constructor:
                has_constructor = True

        if has_constructor:
            _functions = {k:v for (k, v) in self._functions.items() if not v.is_constructor}
            self._functions = _functions

        for function in self._functions_no_params:
            self._functions[function.full_name] = function

        self._functions_no_params = []
        return

    def analyze_content_modifiers(self):
        for modifier in self.modifiers:
            modifier.analyze_content()
        return

    def analyze_content_functions(self):
        for function in self.functions:
            function.analyze_content()
        return


    def convert_expression_to_slithir(self):
        for func in self.functions + self.modifiers:
            if func.contract == self:
                func.generate_slithir_and_analyze()

        all_ssa_state_variables_instances = dict()

        for contract in self.inheritance:
            for v in contract.variables:
                if v.contract == contract:
                    new_var = StateIRVariable(v)
                    all_ssa_state_variables_instances[v.canonical_name] = new_var
                    self._initial_state_variables.append(new_var)

        for v in self.variables:
            if v.contract == self:
                new_var = StateIRVariable(v)
                all_ssa_state_variables_instances[v.canonical_name] = new_var
                self._initial_state_variables.append(new_var)

        for func in self.functions + self.modifiers:
            if func.contract == self:
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


    def __hash__(self):
        return self._id
