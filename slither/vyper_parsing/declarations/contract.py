import logging

from slither.core.declarations.contract import Contract
from slither.vyper_parsing.declarations.function import FunctionVyper
from slither.vyper_parsing.declarations.event import EventVyper
from slither.vyper_parsing.declarations.structure import StructureVyper
from vyper.signatures.event_signature import EventSignature
from vyper.signatures.function_signature import FunctionSignature
from slither.slithir.variables import StateIRVariable

from slither.vyper_parsing.variables.state_variable import StateVariableVyper


logger = logging.getLogger("ContractVyperParsing")

class ContractVyper(Contract):
    def __init__(self, slitherVyper, data):
        super().__init__()

        self.set_slither(slitherVyper)
        self._data = data

        self._functionsNotParsed = []
        # self._modifiersNotParsed = []
        self._functions_no_params = []
        # self._modifiers_no_params = []
        self._eventsNotParsed = []
        self._variablesNotParsed = []
        self._variablesNotParsedByName = {}
        # self._enumsNotParsed = []
        self._structuresNotParsed = []
        # self._usingForNotParsed = []

        self._is_analyzed = False

        # use to remap inheritance id
        # self._remapping = {}

        self._name = self._data['name']
        #
        # self._id = self._data['id']
        #
        # self._inheritance = []

        # self._parse_contract_info()
        self._itemsById = {}
        self._parse_contract_items()

    def get_key(self):
        return self.slither.get_key()

    def _parse_contract_items(self):
        if not 'body' in self._data: # empty contract
            return
        for item in self._data['body']:
            if item[self.get_key()] == 'FunctionDef':
                self._functionsNotParsed.append(item)
            elif item[self.get_key()] == 'EventDef':
                self._eventsNotParsed.append(item)
            elif item[self.get_key()] == 'VariableDeclaration':
                self._variablesNotParsed.append(item)
            elif item[self.get_key()] == 'ClassDef':
                self._structuresNotParsed.append(item)
            else:
                logger.error('Unknown contract item: '+ item[self.get_key()])
                # exit(-1)
            # print(item['name'])
            if 'target' in item:
                self._itemsById[item['target']['id']] = item
            else:
                self._itemsById[item['name']] = item


    def _parse_struct(self, ast_struct, name, code):
        st = StructureVyper(name, ast_struct, code)
        st.set_contract(self)
        # st.set_offset(struct['src'], self.slither)
        self._structures[name] = st

    def parse_structs(self):
        pass
        # print(type(self.slither._global_ctx._globals['funders'].typ.valuetype))
        # for ast_struct in self._structuresNotParsed:
        #     name =ast_struct['name']
        #     # print(self.slither._global_ctx._globals.keys())
        #
        # # for name, code in self.slither._global_ctx._structs.items():
        # #     ast_struct = self._itemsById[name]
        # #     self._parse_struct(ast_struct, name, code)
        #     # self._parse_struct(struct)
        # self._structuresNotParsed = None

    def _parse_function(self, function, functions_def):
        global_ctx = self.slither._global_ctx
        function_sig = FunctionSignature.from_definition(
            functions_def,
            sigs=global_ctx._contracts,
            custom_units=global_ctx._custom_units,
            custom_structs=global_ctx._structs,
            constants=global_ctx._constants
        )
        func = FunctionVyper(function, function_sig, self)
        self.slither.add_function(func)
        self._functions_no_params.append(func)
        func.set_offset({
            'start': function['col_offset'],
            'length':1,
            'filename': self.name,
            'lines' : [function['lineno']]
        }, self.slither)

    def parse_functions(self):

        global_ctx = self.slither._global_ctx
        functions_defs = {function.name : function
            for function in global_ctx._defs}
        for function in self._functionsNotParsed:
            self._parse_function(function, functions_defs[function['name']])

        self._functionsNotParsed = None

        return

    def parse_state_variables(self):
        for key, var_rec in self.slither._global_ctx._globals.items():
            var = StateVariableVyper(var_rec)
            var.set_contract(self)
            ast_node = self._itemsById[var_rec.name]
            target = ast_node['target']
            var.set_offset({
                'start': target['col_offset'],
                'length':1,
                'filename': self.name,
                'lines' : [target['lineno']]
            }, self.slither)
            self._variables[var.name] = var

    # def analyze_structs(self):
    #     for name, l in self.slither._global_ctx._structs.items():
    #         print(name)
    #

    def _analyze_struct(self, struct):
        pass
        # struct.analyze()

    def analyze_structs(self):
        for struct in self.structures:
            struct.analyze()

    def analyze_content_functions(self):
        for function in self.functions:
            function.analyze_content()

    def analyze_events(self):
        for code in self.slither._global_ctx._events:
            event_sig = EventSignature.from_declaration(code, self.slither._global_ctx)
            event = EventVyper(event_sig, self)
            event.analyze()

            ast_node = self._itemsById[event.name]
            target = ast_node['target']
            event.set_offset({
                'start': target['col_offset'],
                'length':1,
                'filename': self.name,
                'lines' : [target['lineno']]
            }, self.slither)
            self._events[event._name] = event

    def analyze_state_variables(self):
        for var in self.variables:
            var.analyze()

    def analyze_params_functions(self):
        for function in self._functions_no_params:
            function.analyze_params()

        self._functions = {function.full_name : function
            for function in self._functions_no_params if function.full_name != '__init__()'}


    @property
    def is_analyzed(self):
        return self._is_analyzed

    def set_is_analyzed(self, is_analyzed):
        self._is_analyzed = is_analyzed

    def convert_expression_to_slithir(self):
        for func in self.functions:
            if func.contract == self:
                func.generate_slithir_and_analyze()

        all_ssa_state_variables_instances = dict()

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

    # endregion
    ###################################################################################
    ###################################################################################
    # region Built in definitions
    ###################################################################################
    ###################################################################################

    def __hash__(self):
        return hash(self.name)

    # endregion
