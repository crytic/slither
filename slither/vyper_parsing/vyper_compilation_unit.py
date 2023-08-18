from typing import Dict
from dataclasses import dataclass, field
from slither.core.declarations import Contract
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.vyper_parsing.declarations.contract import ContractVyper
from slither.analyses.data_dependency.data_dependency import compute_dependency
from slither.vyper_parsing.declarations.struct import Structure
from slither.core.variables.state_variable import StateVariable

from slither.exceptions import SlitherException


@dataclass
class VyperCompilationUnit:
    _compilation_unit: SlitherCompilationUnit
    _parsed: bool = False
    _analyzed: bool = False
    _underlying_contract_to_parser: Dict[Contract, ContractVyper] = field(default_factory=dict)
    _contracts_by_id: Dict[int, Contract] = field(default_factory=dict)

    def parse_module(self, data: Dict, filename: str):
        scope = self._compilation_unit.get_scope(filename)
        contract = Contract(self._compilation_unit, scope)
        contract_parser = ContractVyper(self, contract, data)
        contract.set_offset(data.src, self._compilation_unit)

        self._underlying_contract_to_parser[contract] = contract_parser

    def parse_contracts(self):
        for contract, contract_parser in self._underlying_contract_to_parser.items():
            self._contracts_by_id[contract.id] = contract
            self._compilation_unit.contracts.append(contract)

            contract_parser.parse_enums()
            contract_parser.parse_structs()
            contract_parser.parse_state_variables()
            contract_parser.parse_events()
            contract_parser.parse_functions()

        self._parsed = True

    def analyze_contracts(self) -> None:
        if not self._parsed:
            raise SlitherException("Parse the contract before running analyses")
        for contract, contract_parser in self._underlying_contract_to_parser.items():
            contract_parser.analyze()
        self._convert_to_slithir()

        compute_dependency(self._compilation_unit)

        self._analyzed = True

    def _convert_to_slithir(self) -> None:
        
        for contract in self._compilation_unit.contracts:
            contract.add_constructor_variables()
            for func in contract.functions:
                func.generate_slithir_and_analyze()

    # def __init__(self, compilation_unit: SlitherCompilationUnit) -> None:

    #     self._contracts_by_id: Dict[int, ContractSolc] = {}
    #     self._parsed = False
    #     self._analyzed = False

    #     self._underlying_contract_to_parser: Dict[Contract, ContractSolc] = {}
    #     self._structures_top_level_parser: List[StructureTopLevelSolc] = []
    #     self._custom_error_parser: List[CustomErrorSolc] = []
    #     self._variables_top_level_parser: List[TopLevelVariableSolc] = []
    #     self._functions_top_level_parser: List[FunctionSolc] = []
    #     self._using_for_top_level_parser: List[UsingForTopLevelSolc] = []

    #     self._all_functions_and_modifier_parser: List[FunctionSolc] = []

    #     self._top_level_contracts_counter = 0

    # @property
    # def compilation_unit(self) -> SlitherCompilationUnit:
    #     return self._compilation_unit

    # @property
    # def all_functions_and_modifiers_parser(self) -> List[FunctionSolc]:
    #     return self._all_functions_and_modifier_parser

    # def add_function_or_modifier_parser(self, f: FunctionSolc) -> None:
    #     self._all_functions_and_modifier_parser.append(f)

    # @property
    # def underlying_contract_to_parser(self) -> Dict[Contract, ContractSolc]:
    #     return self._underlying_contract_to_parser

    # @property
    # def slither_parser(self) -> "SlitherCompilationUnitSolc":
    #     return self
