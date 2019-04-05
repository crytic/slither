import logging
import json

from slither.core.slither_core import Slither
from slither.vyper_parsing.declarations.contract import ContractVyper

logger = logging.getLogger("VyperParsing")

class SlitherVyper(Slither):
    def __init__(self, filename):
        super(SlitherVyper, self).__init__()
        self._filename = filename
        self._contractsNotParsed = []
        self._contracts_by_id = {}
        self._analyzed = False
        self._global_ctx = None

    @property
    def analyzed(self):
        return self._analyzed

    def get_key(self):
        return 'vyper_type'

    def _analyze_contracts(self):
        if not self._contractsNotParsed:
            logger.info(f'No contract were found in {self.filename}, check the correct compilation')
        if self._analyzed:
            raise Exception('Contract analysis can be run only once!')

        for contract in self._contractsNotParsed:
            self._parse_struct_var_modifiers_functions(contract)
            self._analyze_struct_events(contract)
            self._analyze_variables_modifiers_functions(contract)
            contract.set_is_analyzed(True)
            self._contracts[contract.name] = contract

        self._analyzed = True

        self._convert_to_slithir()

    def _parse_struct_var_modifiers_functions(self, contract):
        contract.parse_structs()
        contract.parse_state_variables()
        contract.parse_functions()


    def _analyze_struct_events(self, contract):
        # TODO:
        # contract.analyze_constant_state_variables()
        # TODO
        contract.analyze_structs()

        # Event can refer to struct
        contract.analyze_events()


    def _analyze_variables_modifiers_functions(self, contract):

        # TODO
        contract.analyze_params_functions()
        contract.analyze_state_variables()


        # TODO
        contract.analyze_content_functions()

    def _parse_contracts_from_json(self, json_data):
        data_loaded = json.loads(json_data)
        self._parse_contracts_from_loaded_json(data_loaded, data_loaded['name'])

    def _parse_contracts_from_loaded_json(self, data_loaded, filename):
        assert data_loaded[self.get_key()] in ['ContractDef']
        contract = ContractVyper(self, data_loaded)
        contract.set_offset({
            'start': 0,
            'length':0,
            'filename': contract.name,
            'lines' : [0]
        }, self)
        self._contractsNotParsed.append(contract)

    def _convert_to_slithir(self):
        for contract in self.contracts:
            contract.convert_expression_to_slithir()
        self._propagate_function_calls()
        for contract in self.contracts:
            contract.fix_phi()
            contract.update_read_write_using_ssa()
