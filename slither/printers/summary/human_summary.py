"""
Module printing summary of the contract
"""
import logging

from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.code_complexity import compute_cyclomatic_complexity
from slither.utils.colors import green, red, yellow
from slither.utils.standard_libraries import is_standard_library

class PrinterHumanSummary(AbstractPrinter):
    ARGUMENT = 'human-summary'
    HELP = 'Print a human-readable summary of the contracts'

    WIKI = 'https://github.com/trailofbits/slither/wiki/Printer-documentation#human-summary'

    @staticmethod
    def _get_summary_erc20(contract):

        functions_name = [f.name for f in contract.functions]
        state_variables = [v.name for v in contract.state_variables]

        pause = 'pause' in functions_name

        if 'mint' in functions_name:
            if not 'mintingFinished' in state_variables:
                mint_limited = False
            else:
                mint_limited = True
        else:
            mint_limited = None # no minting

        race_condition_mitigated = 'increaseApproval' in functions_name or\
                                   'safeIncreaseAllowance' in functions_name

        return pause, mint_limited, race_condition_mitigated


    def get_summary_erc20(self, contract):
        txt = ''

        pause, mint_limited, race_condition_mitigated = self._get_summary_erc20(contract)

        if pause:
            txt += "\t\t Can be paused? : {}\n".format(yellow('Yes'))
        else:
            txt += "\t\t Can be paused? : {}\n".format(green('No'))

        if mint_limited is None:
            txt += "\t\t Minting restriction? : {}\n".format(green('No Minting'))
        else:
            if mint_limited:
                txt += "\t\t Minting restriction? : {}\n".format(red('Yes'))
            else:
                txt += "\t\t Minting restriction? : {}\n".format(yellow('No'))

        if race_condition_mitigated:
            txt += "\t\t ERC20 race condition mitigation: {}\n".format(green('Yes'))
        else:
            txt += "\t\t ERC20 race condition mitigation: {}\n".format(red('No'))

        return txt

    def _get_detectors_result(self):
        # disable detectors logger
        logger = logging.getLogger('Detectors')
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



        return (len(issues_optimization),
                len(issues_informational),
                len(issues_low),
                len(issues_medium),
                len(issues_high))

    def get_detectors_result(self):
        issues_optimization, issues_informational, issues_low, issues_medium, issues_high = self._get_detectors_result()
        txt = "Number of optimization issues: {}\n".format(green(issues_optimization))
        txt += "Number of informational issues: {}\n".format(green(issues_informational))
        txt += "Number of low issues: {}\n".format(green(issues_low))
        if issues_medium > 0:
            txt += "Number of medium issues: {}\n".format(yellow(issues_medium))
        else:
            txt += "Number of medium issues: {}\n".format(green(issues_medium))
        if issues_high > 0:
            txt += "Number of high issues: {}\n".format(red(issues_high))
        else:
            txt += "Number of high issues: {}\n\n".format(green(issues_high))

        return txt

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

        result = red('Yes') if is_complex else green('No')

        return "\tComplex code? {}\n".format(result)

    @staticmethod
    def _number_functions(contract):
        return len(contract.functions)

    def _lines_number(self):
        if not self.slither.source_code:
            return None
        total_dep_lines = 0
        total_lines = 0
        for filename, source_code in self.slither.source_code.items():
            lines = len(source_code.splitlines())
            is_dep = False
            if self.slither.crytic_compile:
                is_dep = self.slither.crytic_compile.is_dependency(filename)
            if is_dep:
                total_dep_lines += lines
            else:
                total_lines += lines
        return total_lines, total_dep_lines

    def _compilation_type(self):
        if self.slither.crytic_compile is None:
            return 'Compilation non standard\n'
        return f'Compiled with {self.slither.crytic_compile.type}\n'

    def _number_contracts(self):
        if self.slither.crytic_compile is None:
            len(self.slither.contracts), 0
        deps = [c for c in self.slither.contracts if c.is_from_dependency()]
        contracts = [c for c in self.slither.contracts if not c.is_from_dependency()]
        return len(contracts), len(deps)

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

    def output(self, _filename):
        """
        _filename is not used
            Args:
                _filename(string)
        """

        txt = "\n"
        txt += self._compilation_type()

        results = {
            'contracts': {
                "elements": []
            },
            'number_lines': 0,
            'number_lines_in_dependencies': 0,
            'standard_libraries': [],
            'ercs': [],
        }

        lines_number = self._lines_number()
        if lines_number:
            total_lines, total_dep_lines = lines_number
            txt += f'Number of lines: {total_lines} (+ {total_dep_lines} in dependencies)\n'
            results['number_lines'] = total_lines
            results['number_lines__dependencies'] = total_dep_lines

        number_contracts, number_contracts_deps = self._number_contracts()
        txt += f'Number of contracts: {number_contracts} (+ {number_contracts_deps} in dependencies) \n\n'

        txt += self.get_detectors_result()

        libs = self._standard_libraries()
        if libs:
            txt += f'\nUse: {", ".join(libs)}\n'
            results['standard_libraries'] = [str(l) for l in libs]

        ercs = self._ercs()
        if ercs:
            txt += f'ERCs: {", ".join(ercs)}\n'
            results['ercs'] = [str(e) for e in ercs]

        for contract in self.slither.contracts_derived:
            txt += "\nContract {}\n".format(contract.name)
            txt += self.is_complex_code(contract)
            txt += '\tNumber of functions: {}\n'.format(self._number_functions(contract))
            ercs = contract.ercs()
            if ercs:
                txt += '\tERCs: ' + ','.join(ercs) + '\n'
            is_erc20 = contract.is_erc20()
            if is_erc20:
                txt += '\tERC20 info:\n'
                txt += self.get_summary_erc20(contract)

        self.info(txt)

        for contract in self.slither.contracts_derived:
            optimization, info, low, medium, high = self._get_detectors_result()
            contract_d = {'contract_name': contract.name,
                          'is_complex_code': self._is_complex_code(contract),
                          'optimization_issues': optimization,
                          'informational_issues': info,
                          'low_issues': low,
                          'medium_issues': medium,
                          'high_issues': high,
                          'is_erc20': contract.is_erc20(),
                          'number_functions': self._number_functions(contract)}
            if contract_d['is_erc20']:
                pause, mint_limited, race_condition_mitigated = self._get_summary_erc20(contract)
                contract_d['erc20_pause'] = pause
                if mint_limited is not None:
                    contract_d['erc20_can_mint'] = True
                    contract_d['erc20_mint_limited'] = mint_limited
                else:
                    contract_d['erc20_can_mint'] = False
                contract_d['erc20_race_condition_mitigated'] = race_condition_mitigated

            self.add_contract_to_json(contract, results['contracts'], additional_fields=contract_d)

        json = self.generate_json_result(txt, additional_fields=results)

        return json

