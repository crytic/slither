import logging

from slither.core.declarations.contract import Contract
from slither.core.declarations.enum import Enum

from slither.solc_parsing.declarations.structure import StructureSolc
from slither.solc_parsing.declarations.event import EventSolc
from slither.solc_parsing.declarations.modifier import ModifierSolc
from slither.solc_parsing.declarations.function import FunctionSolc

from slither.solc_parsing.variables.state_variable import StateVariableSolc

from slither.solc_parsing.solidity_types.type_parsing import parse_type

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

        # Export info
        self._name = self._data['attributes']['name']
        self._id = self._data['id']
        self._inheritance = []

        self._parse_contract_info()
        self._parse_contract_items()

    @property
    def is_analyzed(self):
        return self._is_analyzed

    def set_is_analyzed(self, is_analyzed):
        self._is_analyzed = is_analyzed

    def _parse_contract_info(self):
        attributes = self._data['attributes']
        self.isInterface = False
        if 'contractKind' in attributes:
            if attributes['contractKind'] == 'interface':
                self.isInterface = True
            self._kind = attributes['contractKind']
        self.linearizedBaseContracts = attributes['linearizedBaseContracts']
        self.fullyImplemented = attributes['fullyImplemented']

    def _parse_contract_items(self):
        if not 'children' in self._data: # empty contract
            return
        for item in self._data['children']:
            if item['name'] == 'FunctionDefinition':
                self._functionsNotParsed.append(item)
            elif item['name'] == 'EventDefinition':
                self._eventsNotParsed.append(item)
            elif item['name'] == 'InheritanceSpecifier':
                # we dont need to parse it as it is redundant
                # with self.linearizedBaseContracts
                continue
            elif item['name'] == 'VariableDeclaration':
                self._variablesNotParsed.append(item)
            elif item['name'] == 'EnumDefinition':
                self._enumsNotParsed.append(item)
            elif item['name'] == 'ModifierDefinition':
                self._modifiersNotParsed.append(item)
            elif item['name'] == 'StructDefinition':
                self._structuresNotParsed.append(item)
            elif item['name'] == 'UsingForDirective':
                self._usingForNotParsed.append(item)
            else:
                logger.error('Unknown contract item: '+item['name'])
                exit(-1)
        return

    def analyze_using_for(self):
        for father in self.inheritance:
            self._using_for.update(father.using_for)

        for using_for in self._usingForNotParsed:
            children = using_for['children']
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
        name = enum['attributes']['name']
        if 'canonicalName' in enum['attributes']:
            canonicalName = enum['attributes']['canonicalName']
        else:
            canonicalName = self.name + '.' + name
        values = []
        for child in enum['children']:
            assert child['name'] == 'EnumValue'
            values.append(child['attributes']['name'])

        new_enum = Enum(name, canonicalName, values)
        new_enum.set_contract(self)
        new_enum.set_offset(enum['src'], self.slither)
        self._enums[canonicalName] = new_enum

    def _parse_struct(self, struct):
        name = struct['attributes']['name']
        if 'canonicalName' in struct['attributes']:
            canonicalName = struct['attributes']['canonicalName']
        else:
            canonicalName = self.name + '.' + name

        if 'children' in struct:
            children = struct['children']
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
            event = EventSolc(event_to_parse)
            event.analyze(self)
            event.set_contract(self)
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

    def analyze_state_variables(self):
        for var in self.variables:
            var.analyze(self)
        return

    def _parse_modifier(self, modifier):

        modif = ModifierSolc(modifier)
        modif.set_contract(self)
        modif.set_offset(modifier['src'], self.slither)
        self._modifiers_no_params.append(modif)

    def parse_modifiers(self):

        for modifier in self._modifiersNotParsed:
            self._parse_modifier(modifier)
        self._modifiersNotParsed = None

        return

    def _parse_function(self, function):
        func = FunctionSolc(function)
        func.set_contract(self)
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
        for function in self._functions_no_params:
            function.analyze_params()
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

    def __hash__(self):
        return self._id
