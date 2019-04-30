import os
import json
import re
import logging

logging.basicConfig()
logger = logging.getLogger("SlitherSolcParsing")
logger.setLevel(logging.INFO)

from slither.solc_parsing.declarations.contract import ContractSolc04
from slither.core.slither_core import Slither
from slither.core.declarations.pragma_directive import Pragma
from slither.core.declarations.import_directive import Import
from slither.analyses.data_dependency.data_dependency import compute_dependency

from slither.utils.colors import red

class SlitherSolc(Slither):

    def __init__(self, filename):
        super(SlitherSolc, self).__init__()
        self._filename = filename
        self._contractsNotParsed = []
        self._contracts_by_id = {}
        self._analyzed = False

        self._is_compact_ast = False


    ###################################################################################
    ###################################################################################
    # region AST
    ###################################################################################
    ###################################################################################

    def get_key(self):
        if self._is_compact_ast:
            return 'nodeType'
        return 'name'

    def get_children(self):
        if self._is_compact_ast:
            return 'nodes'
        return 'children'

    @property
    def is_compact_ast(self):
        return self._is_compact_ast

    # endregion
    ###################################################################################
    ###################################################################################
    # region Parsing
    ###################################################################################
    ###################################################################################

    def _parse_contracts_from_json(self, json_data):
        try:
            data_loaded = json.loads(json_data)
            # Truffle AST
            if 'ast' in data_loaded:
                self._parse_contracts_from_loaded_json(data_loaded['ast'], data_loaded['sourcePath'])
                return True
            # solc AST, where the non-json text was removed
            else:
                if 'attributes' in data_loaded:
                    filename = data_loaded['attributes']['absolutePath']
                else:
                    filename = data_loaded['absolutePath']
                self._parse_contracts_from_loaded_json(data_loaded, filename)
                return True
        except ValueError:

            first = json_data.find('{')
            if first != -1:
                last = json_data.rfind('}') + 1
                filename = json_data[0:first]
                json_data = json_data[first:last]

                data_loaded = json.loads(json_data)
                self._parse_contracts_from_loaded_json(data_loaded, filename)
                return True
            return False

    def _parse_contracts_from_loaded_json(self, data_loaded, filename):
        if 'nodeType' in data_loaded:
            self._is_compact_ast = True

        if 'sourcePaths' in data_loaded:
            for sourcePath in data_loaded['sourcePaths']:
                if os.path.isfile(sourcePath):
                    self._add_source_code(sourcePath)

        if data_loaded[self.get_key()] == 'root':
            self._solc_version = '0.3'
            logger.error('solc <0.4 is not supported')
            return
        elif data_loaded[self.get_key()] == 'SourceUnit':
            self._solc_version = '0.4'
            self._parse_source_unit(data_loaded, filename)
        else:
            logger.error('solc version is not supported')
            return

        for contract_data in data_loaded[self.get_children()]:
            # if self.solc_version == '0.3':
            #     assert contract_data[self.get_key()] == 'Contract'
            #     contract = ContractSolc03(self, contract_data)
            if self.solc_version == '0.4':
                assert contract_data[self.get_key()] in ['ContractDefinition', 'PragmaDirective', 'ImportDirective']
                if contract_data[self.get_key()] == 'ContractDefinition':
                    contract = ContractSolc04(self, contract_data)
                    if 'src' in contract_data:
                        contract.set_offset(contract_data['src'], self)
                    self._contractsNotParsed.append(contract)
                elif contract_data[self.get_key()] == 'PragmaDirective':
                    if self._is_compact_ast:
                        pragma = Pragma(contract_data['literals'])
                    else:
                        pragma = Pragma(contract_data['attributes']["literals"])
                    pragma.set_offset(contract_data['src'], self)
                    self._pragma_directives.append(pragma)
                elif contract_data[self.get_key()] == 'ImportDirective':
                    if self.is_compact_ast:
                        import_directive = Import(contract_data["absolutePath"])
                    else:
                        import_directive = Import(contract_data['attributes']["absolutePath"])
                    import_directive.set_offset(contract_data['src'], self)
                    self._import_directives.append(import_directive)


    def _parse_source_unit(self, data, filename):
        if data[self.get_key()] != 'SourceUnit':
            return -1  # handle solc prior 0.3.6

        # match any char for filename
        # filename can contain space, /, -, ..
        name = re.findall('=* (.+) =*', filename)
        if name:
            assert len(name) == 1
            name = name[0]
        else:
            name = filename

        sourceUnit = -1  # handle old solc, or error
        if 'src' in data:
            sourceUnit = re.findall('[0-9]*:[0-9]*:([0-9]*)', data['src'])
            if len(sourceUnit) == 1:
                sourceUnit = int(sourceUnit[0])

        self._source_units[sourceUnit] = name
        if os.path.isfile(name) and not name in self.source_code:
            self._add_source_code(name)
        else:
            lib_name = os.path.join('node_modules', name)
            if os.path.isfile(lib_name) and not name in self.source_code:
                self._add_source_code(lib_name)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Analyze
    ###################################################################################
    ###################################################################################

    @property
    def analyzed(self):
        return self._analyzed

    def _analyze_contracts(self):
        if not self._contractsNotParsed:
            logger.info(f'No contract were found in {self.filename}, check the correct compilation') 
        if self._analyzed:
            raise Exception('Contract analysis can be run only once!')

        # First we save all the contracts in a dict
        # the key is the contractid
        for contract in self._contractsNotParsed:
            if contract.name in self._contracts:
                if contract.id != self._contracts[contract.name].id:
                    info = 'Slither does not handle projects with contract names re-use'
                    info += '\n{} is defined in:'.format(contract.name)
                    info += '\n- {}\n- {}'.format(contract.source_mapping_str,
                                               self._contracts[contract.name].source_mapping_str)
                    logger.error(info)
                    exit(-1)
            else:
                self._contracts_by_id[contract.id] = contract
                self._contracts[contract.name] = contract

        # Update of the inheritance 
        for contract in self._contractsNotParsed:
            # remove the first elem in linearizedBaseContracts as it is the contract itself
            ancestors = []
            fathers = []
            father_constructors = []
            try:
                # Resolve linearized base contracts.
                for i in contract.linearizedBaseContracts[1:]:
                    if i in contract.remapping:
                        ancestors.append(self.get_contract_from_name(contract.remapping[i]))
                    else:
                        ancestors.append(self._contracts_by_id[i])

                # Resolve immediate base contracts
                for i in contract.baseContracts:
                    if i in contract.remapping:
                        fathers.append(self.get_contract_from_name(contract.remapping[i]))
                    else:
                        fathers.append(self._contracts_by_id[i])

                # Resolve immediate base constructor calls
                for i in contract.baseConstructorContractsCalled:
                    if i in contract.remapping:
                        father_constructors.append(self.get_contract_from_name(contract.remapping[i]))
                    else:
                        father_constructors.append(self._contracts_by_id[i])

            except KeyError:
                logger.error(red('A contract was not found, it is likely that your codebase contains muliple contracts with the same name'))
                logger.error(red('Truffle does not handle this case during compilation'))
                logger.error(red('Please read https://github.com/trailofbits/slither/wiki#keyerror-or-nonetype-error'))
                logger.error(red('And update your code to remove the duplicate'))
                exit(-1)
            contract.setInheritance(ancestors, fathers, father_constructors)

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

        self._analyzed = True

        self._convert_to_slithir()

        compute_dependency(self)


    def _analyze_all_enums(self, contracts_to_be_analyzed):
        while contracts_to_be_analyzed:
            contract = contracts_to_be_analyzed[0]

            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            all_father_analyzed = all(father.is_analyzed for father in contract.inheritance)

            if not contract.inheritance or all_father_analyzed:
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
            all_father_analyzed = all(father.is_analyzed for father in contract.inheritance)

            if not contract.inheritance or all_father_analyzed:
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
            all_father_analyzed = all(father.is_analyzed for father in contract.inheritance)

            if not contract.inheritance or all_father_analyzed:
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
            all_father_analyzed = all(father.is_analyzed for father in contract.inheritance)

            if not contract.inheritance or all_father_analyzed:
                self._analyze_variables_modifiers_functions(contract)

            else:
                contracts_to_be_analyzed += [contract]
        return

    def _analyze_enums(self, contract):
        # Enum must be analyzed first
        contract.analyze_enums()
        contract.set_is_analyzed(True)

    def _parse_struct_var_modifiers_functions(self, contract):
        contract.parse_structs()  # struct can refer another struct
        contract.parse_state_variables()
        contract.parse_modifiers()
        contract.parse_functions()
        contract.set_is_analyzed(True)

    def _analyze_struct_events(self, contract):

        contract.analyze_constant_state_variables()

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

    def _convert_to_slithir(self):
        for contract in self.contracts:
            contract.convert_expression_to_slithir()
        self._propagate_function_calls()
        for contract in self.contracts:
            contract.fix_phi()
            contract.update_read_write_using_ssa()

    # endregion
