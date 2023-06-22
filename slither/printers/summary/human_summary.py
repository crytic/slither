"""
Module printing summary of the contract
"""
import logging
from typing import Tuple, List, Dict

from slither.core.declarations import SolidityFunction, Function
from slither.core.variables.state_variable import StateVariable
from slither.printers.abstract_printer import AbstractPrinter
from slither.printers.summary.loc import compute_loc_metrics
from slither.slithir.operations import (
    LowLevelCall,
    HighLevelCall,
    Transfer,
    Send,
    SolidityCall,
)
from slither.utils import output
from slither.utils.code_complexity import compute_cyclomatic_complexity
from slither.utils.colors import green, red, yellow
from slither.utils.myprettytable import MyPrettyTable
from slither.utils.standard_libraries import is_standard_library
from slither.core.cfg.node import NodeType


class PrinterHumanSummary(AbstractPrinter):
    ARGUMENT = "human-summary"
    HELP = "Print a human-readable summary of the contracts"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#human-summary"

    @staticmethod
    def _get_summary_erc20(contract):
        functions_name = [f.name for f in contract.functions]
        state_variables = [v.name for v in contract.state_variables]

        pause = "pause" in functions_name

        if "mint" in functions_name:
            if "mintingFinished" in state_variables:
                mint_unlimited = False
            else:
                mint_unlimited = True
        else:
            mint_unlimited = None  # no minting

        race_condition_mitigated = (
            "increaseApproval" in functions_name or "safeIncreaseAllowance" in functions_name
        )

        return pause, mint_unlimited, race_condition_mitigated

    def get_summary_erc20(self, contract):
        txt = ""

        pause, mint_unlimited, race_condition_mitigated = self._get_summary_erc20(contract)

        if pause:
            txt += yellow("Pausable") + "\n"

        if mint_unlimited is None:
            txt += green("No Minting") + "\n"
        else:
            if mint_unlimited:
                txt += red("∞ Minting") + "\n"
            else:
                txt += yellow("Minting") + "\n"

        if not race_condition_mitigated:
            txt += red("Approve Race Cond.") + "\n"

        return txt

    def _get_detectors_result(self) -> Tuple[List[Dict], int, int, int, int, int]:
        # disable detectors logger
        logger = logging.getLogger("Detectors")
        logger.setLevel(logging.ERROR)

        checks_optimization = self.slither.detectors_optimization
        checks_informational = self.slither.detectors_informational
        checks_low = self.slither.detectors_low
        checks_medium = self.slither.detectors_medium
        checks_high = self.slither.detectors_high

        issues_optimization = [c.detect() for c in checks_optimization]
        issues_optimization = [c for c in issues_optimization if c]
        issues_optimization = [item for sublist in issues_optimization for item in sublist]

        issues_informational = [c.detect() for c in checks_informational]
        issues_informational = [c for c in issues_informational if c]
        issues_informational = [item for sublist in issues_informational for item in sublist]

        issues_low = [c.detect() for c in checks_low]
        issues_low = [c for c in issues_low if c]
        issues_low = [item for sublist in issues_low for item in sublist]

        issues_medium = (c.detect() for c in checks_medium)
        issues_medium = [c for c in issues_medium if c]
        issues_medium = [item for sublist in issues_medium for item in sublist]

        issues_high = [c.detect() for c in checks_high]
        issues_high = [c for c in issues_high if c]
        issues_high = [item for sublist in issues_high for item in sublist]

        all_results = (
            issues_optimization + issues_informational + issues_low + issues_medium + issues_high
        )

        return (
            all_results,
            len(issues_optimization),
            len(issues_informational),
            len(issues_low),
            len(issues_medium),
            len(issues_high),
        )

    def get_detectors_result(self) -> Tuple[str, List[Dict], int, int, int, int, int]:
        (
            all_results,
            optimization,
            informational,
            low,
            medium,
            high,
        ) = self._get_detectors_result()
        txt = f"Number of optimization issues: {green(optimization)}\n"
        txt += f"Number of informational issues: {green(informational)}\n"
        txt += f"Number of low issues: {green(low)}\n"
        if medium > 0:
            txt += f"Number of medium issues: {yellow(medium)}\n"
        else:
            txt += f"Number of medium issues: {green(medium)}\n"
        if high > 0:
            txt += f"Number of high issues: {red(high)}\n"
        else:
            txt += f"Number of high issues: {green(high)}\n\n"

        return txt, all_results, optimization, informational, low, medium, high

    @staticmethod
    def _is_complex_code(contract):
        for f in contract.functions:
            if compute_cyclomatic_complexity(f) > 7:
                return True
        return False

    def is_complex_code(self, contract):
        """
            Check if the code is complex
            Heuristic, the code is complex if:
                - One function has a cyclomatic complexity > 7
        Args:
            contract
        """

        is_complex = self._is_complex_code(contract)

        result = red("Yes") if is_complex else green("No")
        return result

    @staticmethod
    def _number_functions(contract):
        return len(contract.functions)

    def _get_number_of_assembly_lines(self) -> int:
        total_asm_lines = 0
        for contract in self.contracts:
            for function in contract.functions_declared:
                for node in function.nodes:
                    if node.type == NodeType.ASSEMBLY:
                        inline_asm = node.inline_asm
                        if inline_asm:
                            total_asm_lines += len(inline_asm.splitlines())
        return total_asm_lines

    def _compilation_type(self):
        if self.slither.crytic_compile is None:
            return "Compilation non standard\n"
        return f"Compiled with {str(self.slither.crytic_compile.type)}\n"

    def _number_contracts(self) -> Tuple[int, int, int]:
        contracts = self.slither.contracts
        deps = [c for c in contracts if c.is_from_dependency()]
        tests = [c for c in contracts if c.is_test]
        return len(contracts) - len(deps) - len(tests), len(deps), len(tests)

    def _standard_libraries(self):
        libraries = []
        for contract in self.contracts:
            lib = is_standard_library(contract)
            if lib:
                libraries.append(lib)

        return libraries

    def _ercs(self):
        ercs = []
        for contract in self.contracts:
            ercs += contract.ercs()
        return list(set(ercs))

    def _get_features(self, contract):  # pylint: disable=too-many-branches
        has_payable = False
        can_send_eth = False
        can_selfdestruct = False
        has_ecrecover = False
        can_delegatecall = False
        has_token_interaction = False

        has_assembly = False

        use_abi_encoder = False

        for compilation_unit in self.slither.compilation_units:
            for pragma in compilation_unit.pragma_directives:
                if (
                    pragma.source_mapping.filename.absolute
                    == contract.source_mapping.filename.absolute
                ):
                    if pragma.is_abi_encoder_v2:
                        use_abi_encoder = True

        for function in contract.functions:
            if function.payable:
                has_payable = True

            if function.contains_assembly:
                has_assembly = True

            for ir in function.slithir_operations:
                if isinstance(ir, (LowLevelCall, HighLevelCall, Send, Transfer)) and ir.call_value:
                    can_send_eth = True
                if isinstance(ir, SolidityCall) and ir.function in [
                    SolidityFunction("suicide(address)"),
                    SolidityFunction("selfdestruct(address)"),
                ]:
                    can_selfdestruct = True
                if isinstance(ir, SolidityCall) and ir.function == SolidityFunction(
                    "ecrecover(bytes32,uint8,bytes32,bytes32)"
                ):
                    has_ecrecover = True
                if isinstance(ir, LowLevelCall) and ir.function_name in [
                    "delegatecall",
                    "callcode",
                ]:
                    can_delegatecall = True
                if isinstance(ir, HighLevelCall):
                    if (
                        isinstance(ir.function, (Function, StateVariable))
                        and ir.function.contract.is_possible_token
                    ):
                        has_token_interaction = True

        return {
            "Receive ETH": has_payable,
            "Send ETH": can_send_eth,
            "Selfdestruct": can_selfdestruct,
            "Ecrecover": has_ecrecover,
            "Delegatecall": can_delegatecall,
            "Tokens interaction": has_token_interaction,
            "AbiEncoderV2": use_abi_encoder,
            "Assembly": has_assembly,
            "Upgradeable": contract.is_upgradeable,
            "Proxy": contract.is_upgradeable_proxy,
        }

    def _get_contracts(self, txt: str) -> str:
        (
            number_contracts,
            number_contracts_deps,
            number_contracts_tests,
        ) = self._number_contracts()
        txt += f"Total number of contracts in source files: {number_contracts}\n"
        if number_contracts_deps > 0:
            txt += f"Number of contracts in dependencies: {number_contracts_deps}\n"
        if number_contracts_tests > 0:
            txt += f"Number of contracts in tests       : {number_contracts_tests}\n"
        return txt

    def _get_number_lines(self, txt: str, results: Dict) -> Tuple[str, Dict]:
        loc = compute_loc_metrics(self.slither)
        txt += "Source lines of code (SLOC) in source files: "
        txt += f"{loc.src.sloc}\n"
        if loc.dep.sloc > 0:
            txt += "Source lines of code (SLOC) in dependencies: "
            txt += f"{loc.dep.sloc}\n"
        if loc.test.sloc > 0:
            txt += "Source lines of code (SLOC) in tests       : "
            txt += f"{loc.test.sloc}\n"
        results["number_lines"] = loc.src.sloc
        results["number_lines__dependencies"] = loc.dep.sloc
        total_asm_lines = self._get_number_of_assembly_lines()
        txt += f"Number of  assembly lines: {total_asm_lines}\n"
        results["number_lines_assembly"] = total_asm_lines
        return txt, results

    def output(self, _filename):  # pylint: disable=too-many-locals,too-many-statements
        """
        _filename is not used
            Args:
                _filename(string)
        """

        txt = "\n"
        txt += self._compilation_type()

        results = {
            "contracts": {"elements": []},
            "number_lines": 0,
            "number_lines_in_dependencies": 0,
            "number_lines_assembly": 0,
            "standard_libraries": [],
            "ercs": [],
            "number_findings": {},
            "detectors": [],
        }
        txt = self._get_contracts(txt)
        txt, results = self._get_number_lines(txt, results)
        (
            txt_detectors,
            detectors_results,
            optimization,
            info,
            low,
            medium,
            high,
        ) = self.get_detectors_result()
        txt += txt_detectors

        results["number_findings"] = {
            "optimization_issues": optimization,
            "informational_issues": info,
            "low_issues": low,
            "medium_issues": medium,
            "high_issues": high,
        }
        results["detectors"] = detectors_results

        libs = self._standard_libraries()
        if libs:
            txt += f'\nUse: {", ".join(libs)}\n'
            results["standard_libraries"] = [str(lib) for lib in libs]

        ercs = self._ercs()
        if ercs:
            txt += f'ERCs: {", ".join(ercs)}\n'
            results["ercs"] = [str(e) for e in ercs]

        table = MyPrettyTable(
            ["Name", "# functions", "ERCS", "ERC20 info", "Complex code", "Features"]
        )
        for contract in self.slither.contracts_derived:
            if contract.is_from_dependency() or contract.is_test:
                continue

            is_complex = self.is_complex_code(contract)
            number_functions = self._number_functions(contract)
            ercs = ",".join(contract.ercs())
            is_erc20 = contract.is_erc20()
            erc20_info = ""
            if is_erc20:
                erc20_info += self.get_summary_erc20(contract)

            features = "\n".join(
                [name for name, to_print in self._get_features(contract).items() if to_print]
            )

            table.add_row(
                [
                    contract.name,
                    number_functions,
                    ercs,
                    erc20_info,
                    is_complex,
                    features,
                ]
            )

        self.info(txt + "\n" + str(table))

        results_contract = output.Output("")
        for contract in self.slither.contracts_derived:
            if contract.is_test or contract.is_from_dependency():
                continue

            contract_d = {
                "contract_name": contract.name,
                "is_complex_code": self._is_complex_code(contract),
                "is_erc20": contract.is_erc20(),
                "number_functions": self._number_functions(contract),
                "features": [
                    name for name, to_print in self._get_features(contract).items() if to_print
                ],
            }
            if contract_d["is_erc20"]:
                pause, mint_limited, race_condition_mitigated = self._get_summary_erc20(contract)
                contract_d["erc20_pause"] = pause
                if mint_limited is not None:
                    contract_d["erc20_can_mint"] = True
                    contract_d["erc20_mint_limited"] = mint_limited
                else:
                    contract_d["erc20_can_mint"] = False
                contract_d["erc20_race_condition_mitigated"] = race_condition_mitigated
            results_contract.add_contract(contract, additional_fields=contract_d)

        results["contracts"]["elements"] = results_contract.elements

        json = self.generate_output(txt, additional_fields=results)

        return json
