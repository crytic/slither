import json
import re
import logging

logger = logging.getLogger("SlitherSolcParsing")

from slither.solcParsing.declarations.contractSolc04 import ContractSolc04
from slither.core.slitherCore import Slither

class SlitherSolc(Slither):

    def __init__(self, filename):
        super(SlitherSolc, self).__init__()
        self._filename = filename
        self._contractsNotParsed = []
        self._contracts_by_id = {}

    def parse_contracts_from_json(self, json_data):
        first = json_data.find('{')
        if first != -1:
            last = json_data.rfind('}') +1
            filename = json_data[0:first]
            json_data = json_data[first:last]

            data_loaded = json.loads(json_data)

            if data_loaded['name'] == 'root':
                self._solc_version = '0.3'
                logger.error('solc <0.4 not supported')
                exit(-1)
            elif data_loaded['name'] == 'SourceUnit':
                self._solc_version = '0.4'
                self._parse_source_unit(data_loaded, filename)
            else:
                logger.error('solc version not supported')
                exit(-1)

            for contract_data in data_loaded['children']:
#                if self.solc_version == '0.3':
#                    assert contract_data['name'] == 'Contract'
 #                   contract = ContractSolc03(self, contract_data)
                if self.solc_version == '0.4':
                    assert contract_data['name'] in ['ContractDefinition', 'PragmaDirective', 'ImportDirective']
                    if contract_data['name'] == 'ContractDefinition':
                        contract = ContractSolc04(self, contract_data)
                        self._contractsNotParsed.append(contract)
                    elif contract_data['name'] == 'PragmaDirective':
                        self._pragma_directives.append(contract_data['attributes']["literals"])
                    elif contract_data['name'] == 'ImportDirective':
                        self._import_directives.append(contract_data['attributes']["absolutePath"])

            return True
        return False

    def _parse_source_unit(self, data, filename):
        if data['name'] != 'SourceUnit':
            return -1 # handle solc prior 0.3.6

        # match any char for filename
        # filename can contain space, /, -, ..
        name = re.findall('=* (.+) =*', filename)
        assert len(name) == 1
        name = name[0]

        sourceUnit = -1 # handle old solc, or error
        if 'src' in data:
            sourceUnit = re.findall('[0-9]*:[0-9]*:([0-9]*)', data['src'])
            if len(sourceUnit) == 1:
                sourceUnit = int(sourceUnit[0])

        self._source_units[sourceUnit] = name

    def analyze_contracts(self):

        # First we save all the contracts in a dict
        # the key is the contractid
        for contract in self._contractsNotParsed:
            self._contracts_by_id[contract.id] = contract
            self._contracts[contract.name] = contract

        # Update of the inheritances 
        for contract in self._contractsNotParsed:
            # remove the first elem in linearizedBaseContracts as it is the contract itself
            contract.setInheritances([self._contracts_by_id[i] for i in contract.linearizedBaseContracts[1:]])

        contracts_to_be_analyzed = self.contracts

        # Any contract can refer another contract enum without need for inheritance
        self._analyze_all_enums(contracts_to_be_analyzed)
        [c.set_is_analyzed(False) for c in self.contracts]

        libraries = [c for c in contracts_to_be_analyzed if c.contract_kind == 'library']
        contracts_to_be_analyzed = [c for c in contracts_to_be_analyzed if c.contract_kind != 'library']

        # We first parse the struct/variables/functions/contract
        self._analyze_first_part(contracts_to_be_analyzed, libraries)
        [c.set_is_analyzed(False) for c in self.contracts]

        # We analyze the struct and parse and analyze the events
        # A contract can refer in the variables a struct or a event from any contract
        # (without inheritance link)
        self._analyze_second_part(contracts_to_be_analyzed, libraries)
        [c.set_is_analyzed(False) for c in self.contracts]

        # Then we analyse state variables, functions and modifiers
        self._analyze_third_part(contracts_to_be_analyzed, libraries)


    # TODO refactor the following functions, and use a lambda function

    def _analyze_all_enums(self, contracts_to_be_analyzed):
        while contracts_to_be_analyzed:
            contract = contracts_to_be_analyzed[0]

            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            all_father_analyzed = all(father.is_analyzed for father in contract.inheritances)

            if not contract.inheritances or all_father_analyzed:
                self._analyze_enums(contract)
            else:
                contracts_to_be_analyzed += [contract]
        return


    def _analyze_first_part(self, contracts_to_be_analyzed, libraries):
        for lib in libraries:
            self._parse_struct_var_modifiers_functions(lib)

        # Start with the contracts without inheritance
        # Analyze a contract only if all its fathers
        # Were analyzed
        while contracts_to_be_analyzed:

            contract = contracts_to_be_analyzed[0]

            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            all_father_analyzed = all(father.is_analyzed for father in contract.inheritances)

            if not contract.inheritances or all_father_analyzed:
                self._parse_struct_var_modifiers_functions(contract)

            else:
                contracts_to_be_analyzed += [contract]
        return


    def _analyze_second_part(self, contracts_to_be_analyzed, libraries):
        for lib in libraries:
            self._analyze_struct_events(lib)

        # Start with the contracts without inheritance
        # Analyze a contract only if all its fathers
        # Were analyzed
        while contracts_to_be_analyzed:

            contract = contracts_to_be_analyzed[0]

            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            all_father_analyzed = all(father.is_analyzed for father in contract.inheritances)

            if not contract.inheritances or all_father_analyzed:
                self._analyze_struct_events(contract)

            else:
                contracts_to_be_analyzed += [contract]
        return

    def _analyze_third_part(self, contracts_to_be_analyzed, libraries):
        for lib in libraries:
            self._analyze_variables_modifiers_functions(lib)

        # Start with the contracts without inheritance
        # Analyze a contract only if all its fathers
        # Were analyzed
        while contracts_to_be_analyzed:

            contract = contracts_to_be_analyzed[0]

            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            all_father_analyzed = all(father.is_analyzed for father in contract.inheritances)

            if not contract.inheritances or all_father_analyzed:
                self._analyze_variables_modifiers_functions(contract)

            else:
                contracts_to_be_analyzed += [contract]
        return

    def _analyze_enums(self, contract):
        # Enum must be analyzed first
        contract.analyze_enums()
        contract.set_is_analyzed(True)

    def _parse_struct_var_modifiers_functions(self, contract):
        contract.parse_structs() # struct can refer another struct
        contract.parse_state_variables()
        contract.parse_modifiers()
        contract.parse_functions()
        contract.set_is_analyzed(True)

    def _analyze_struct_events(self, contract):
        # Struct can refer to enum, or state variables
        contract.analyze_structs()
        # Event can refer to struct
        contract.analyze_events()

        contract.analyze_using_for()

        contract.set_is_analyzed(True)

    def _analyze_variables_modifiers_functions(self, contract):
        # State variables, modifiers and functions can refer to anything

        contract.analyze_params_modifiers()
        contract.analyze_params_functions()

        contract.analyze_state_variables()

        contract.analyze_content_modifiers()
        contract.analyze_content_functions()

        contract.set_is_analyzed(True)

