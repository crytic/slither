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
from .declarations.contract import ContractVyper
from slither.utils.colors import red



class SlitherVyper(Slither):

    def __init__(self, filename):
        super(SlitherVyper, self).__init__()
        self._filename = filename
        self._contractsNotParsed = []
        self._contracts_by_id = {}
        self._analyzed = False

    @property
    def language(self):
        return 'Vyper'

    # endregion
    ###################################################################################
    ###################################################################################
    # region Parsing
    ###################################################################################
    ###################################################################################


    def _parse_contracts_from_loaded_json(self, data_loaded, filename):
        contract = ContractVyper(self, data_loaded)
        contract.set_offset(None, self)
        self._contracts = {contract.name: contract}


        other_contracts = [ContractVyper(self, c) for c in data_loaded['ast'] if c['ast_type'] == 'ClassDef' \
                           and c['class_type'] == 'contract']
        for other_contract in other_contracts:
            other_contract.set_offset(None, self)
            self._contracts[other_contract.name] = other_contract


    #
    # # endregion
    # ###################################################################################
    # ###################################################################################
    # # region Analyze
    # ###################################################################################
    # ###################################################################################
    #
    # @property
    # def analyzed(self):
    #     return self._analyzed
    #
    def _analyze_contracts(self):
        return
    #     if not self._contractsNotParsed:
    #         logger.info(f'No contract were found in {self.filename}, check the correct compilation')
    #     if self._analyzed:
    #         raise Exception('Contract analysis can be run only once!')
    #
    #     # First we save all the contracts in a dict
    #     # the key is the contractid
    #     for contract in self._contractsNotParsed:
    #         if contract.name in self._contracts:
    #             if contract.id != self._contracts[contract.name].id:
    #                 info = 'Slither does not handle projects with contract names re-use'
    #                 info += '\n{} is defined in:'.format(contract.name)
    #                 info += '\n- {}\n- {}'.format(contract.source_mapping_str,
    #                                            self._contracts[contract.name].source_mapping_str)
    #                 raise ParsingNameReuse(info)
    #         else:
    #             self._contracts_by_id[contract.id] = contract
    #             self._contracts[contract.name] = contract
    #
    #     # Update of the inheritance
    #     for contract in self._contractsNotParsed:
    #         # remove the first elem in linearizedBaseContracts as it is the contract itself
    #         ancestors = []
    #         fathers = []
    #         father_constructors = []
    #         try:
    #             # Resolve linearized base contracts.
    #             for i in contract.linearizedBaseContracts[1:]:
    #                 if i in contract.remapping:
    #                     ancestors.append(self.get_contract_from_name(contract.remapping[i]))
    #                 else:
    #                     ancestors.append(self._contracts_by_id[i])
    #
    #             # Resolve immediate base contracts
    #             for i in contract.baseContracts:
    #                 if i in contract.remapping:
    #                     fathers.append(self.get_contract_from_name(contract.remapping[i]))
    #                 else:
    #                     fathers.append(self._contracts_by_id[i])
    #
    #             # Resolve immediate base constructor calls
    #             for i in contract.baseConstructorContractsCalled:
    #                 if i in contract.remapping:
    #                     father_constructors.append(self.get_contract_from_name(contract.remapping[i]))
    #                 else:
    #                     father_constructors.append(self._contracts_by_id[i])
    #
    #         except KeyError:
    #             txt = 'A contract was not found, it is likely that your codebase contains muliple contracts with the same name'
    #             txt += 'Truffle does not handle this case during compilation'
    #             txt += 'Please read https://github.com/trailofbits/slither/wiki#keyerror-or-nonetype-error'
    #             txt += 'And update your code to remove the duplicate'
    #             raise ParsingContractNotFound(txt)
    #         contract.setInheritance(ancestors, fathers, father_constructors)
    #
    #     contracts_to_be_analyzed = self.contracts
    #
    #     # Any contract can refer another contract enum without need for inheritance
    #     self._analyze_all_enums(contracts_to_be_analyzed)
    #     [c.set_is_analyzed(False) for c in self.contracts]
    #
    #     libraries = [c for c in contracts_to_be_analyzed if c.contract_kind == 'library']
    #     contracts_to_be_analyzed = [c for c in contracts_to_be_analyzed if c.contract_kind != 'library']
    #
    #     # We first parse the struct/variables/functions/contract
    #     self._analyze_first_part(contracts_to_be_analyzed, libraries)
    #     [c.set_is_analyzed(False) for c in self.contracts]
    #
    #     # We analyze the struct and parse and analyze the events
    #     # A contract can refer in the variables a struct or a event from any contract
    #     # (without inheritance link)
    #     self._analyze_second_part(contracts_to_be_analyzed, libraries)
    #     [c.set_is_analyzed(False) for c in self.contracts]
    #
    #     # Then we analyse state variables, functions and modifiers
    #     self._analyze_third_part(contracts_to_be_analyzed, libraries)
    #
    #     self._analyzed = True
    #
    #     self._convert_to_slithir()
    #
    #     compute_dependency(self)
    #
    #
    # def _analyze_all_enums(self, contracts_to_be_analyzed):
    #     while contracts_to_be_analyzed:
    #         contract = contracts_to_be_analyzed[0]
    #
    #         contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
    #         all_father_analyzed = all(father.is_analyzed for father in contract.inheritance)
    #
    #         if not contract.inheritance or all_father_analyzed:
    #             self._analyze_enums(contract)
    #         else:
    #             contracts_to_be_analyzed += [contract]
    #     return
    #
    # def _analyze_first_part(self, contracts_to_be_analyzed, libraries):
    #     for lib in libraries:
    #         self._parse_struct_var_modifiers_functions(lib)
    #
    #     # Start with the contracts without inheritance
    #     # Analyze a contract only if all its fathers
    #     # Were analyzed
    #     while contracts_to_be_analyzed:
    #
    #         contract = contracts_to_be_analyzed[0]
    #
    #         contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
    #         all_father_analyzed = all(father.is_analyzed for father in contract.inheritance)
    #
    #         if not contract.inheritance or all_father_analyzed:
    #             self._parse_struct_var_modifiers_functions(contract)
    #
    #         else:
    #             contracts_to_be_analyzed += [contract]
    #     return
    #
    # def _analyze_second_part(self, contracts_to_be_analyzed, libraries):
    #     for lib in libraries:
    #         self._analyze_struct_events(lib)
    #
    #     # Start with the contracts without inheritance
    #     # Analyze a contract only if all its fathers
    #     # Were analyzed
    #     while contracts_to_be_analyzed:
    #
    #         contract = contracts_to_be_analyzed[0]
    #
    #         contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
    #         all_father_analyzed = all(father.is_analyzed for father in contract.inheritance)
    #
    #         if not contract.inheritance or all_father_analyzed:
    #             self._analyze_struct_events(contract)
    #
    #         else:
    #             contracts_to_be_analyzed += [contract]
    #     return
    #
    # def _analyze_third_part(self, contracts_to_be_analyzed, libraries):
    #     for lib in libraries:
    #         self._analyze_variables_modifiers_functions(lib)
    #
    #     # Start with the contracts without inheritance
    #     # Analyze a contract only if all its fathers
    #     # Were analyzed
    #     while contracts_to_be_analyzed:
    #
    #         contract = contracts_to_be_analyzed[0]
    #
    #         contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
    #         all_father_analyzed = all(father.is_analyzed for father in contract.inheritance)
    #
    #         if not contract.inheritance or all_father_analyzed:
    #             self._analyze_variables_modifiers_functions(contract)
    #
    #         else:
    #             contracts_to_be_analyzed += [contract]
    #     return
    #
    # def _analyze_enums(self, contract):
    #     # Enum must be analyzed first
    #     contract.analyze_enums()
    #     contract.set_is_analyzed(True)
    #
    # def _parse_struct_var_modifiers_functions(self, contract):
    #     contract.parse_structs()  # struct can refer another struct
    #     contract.parse_state_variables()
    #     contract.parse_modifiers()
    #     contract.parse_functions()
    #     contract.set_is_analyzed(True)
    #
    # def _analyze_struct_events(self, contract):
    #
    #     contract.analyze_constant_state_variables()
    #
    #     # Struct can refer to enum, or state variables
    #     contract.analyze_structs()
    #     # Event can refer to struct
    #     contract.analyze_events()
    #
    #     contract.analyze_using_for()
    #
    #     contract.set_is_analyzed(True)
    #
    # def _analyze_variables_modifiers_functions(self, contract):
    #     # State variables, modifiers and functions can refer to anything
    #
    #     contract.analyze_params_modifiers()
    #     contract.analyze_params_functions()
    #
    #     contract.analyze_state_variables()
    #
    #     contract.analyze_content_modifiers()
    #     contract.analyze_content_functions()
    #
    #
    #
    #     contract.set_is_analyzed(True)
    #
    # def _convert_to_slithir(self):
    #
    #     for contract in self.contracts:
    #         contract.add_constructor_variables()
    #         contract.convert_expression_to_slithir()
    #     self._propagate_function_calls()
    #     for contract in self.contracts:
    #         contract.fix_phi()
    #         contract.update_read_write_using_ssa()

    # endregion
