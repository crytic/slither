from typing import Dict
import os
import re
from dataclasses import dataclass, field
from slither.core.declarations import Contract
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.vyper_parsing.declarations.contract import ContractVyper
from slither.analyses.data_dependency.data_dependency import compute_dependency
from slither.vyper_parsing.ast.types import Module
from slither.exceptions import SlitherException


@dataclass
class VyperCompilationUnit:
    _compilation_unit: SlitherCompilationUnit
    _parsed: bool = False
    _analyzed: bool = False
    _underlying_contract_to_parser: Dict[Contract, ContractVyper] = field(default_factory=dict)
    _contracts_by_id: Dict[int, Contract] = field(default_factory=dict)

    def parse_module(self, data: Module, filename: str):

        sourceUnit_candidates = re.findall("[0-9]*:[0-9]*:([0-9]*)", data.src)
        assert len(sourceUnit_candidates) == 1, "Source unit not found"
        sourceUnit = int(sourceUnit_candidates[0])

        self._compilation_unit.source_units[sourceUnit] = filename
        if os.path.isfile(filename) and filename not in self._compilation_unit.core.source_code:
            self._compilation_unit.core.add_source_code(filename)

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

        for contract_parser in self._underlying_contract_to_parser.values():
            # State variables are analyzed for all contracts because interfaces may
            # reference them, specifically, constants.
            contract_parser.analyze_state_variables()

        for contract_parser in self._underlying_contract_to_parser.values():
            contract_parser.analyze()

        self._convert_to_slithir()

        compute_dependency(self._compilation_unit)

        self._analyzed = True

    def _convert_to_slithir(self) -> None:
        for contract in self._compilation_unit.contracts:
            contract.add_constructor_variables()
            for func in contract.functions:
                func.generate_slithir_and_analyze()

            contract.convert_expression_to_slithir_ssa()

        self._compilation_unit.propagate_function_calls()
        for contract in self._compilation_unit.contracts:
            contract.fix_phi()
            contract.update_read_write_using_ssa()
