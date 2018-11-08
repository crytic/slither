"""
Module printing summary of the contract
"""
import logging

from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.code_complexity import compute_cyclomatic_complexity
from slither.utils.colors import green, red, yellow


class PrinterHumanSummary(AbstractPrinter):
    ARGUMENT = 'human-summary'
    HELP = 'Print a human readable summary of the contracts'

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
            mint = None # no minting

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

        checks_informational = self.slither.detectors_informational
        checks_low = self.slither.detectors_low
        checks_medium = self.slither.detectors_medium
        checks_high = self.slither.detectors_high

        issues_informational = [c.detect() for c in checks_informational]
        issues_informational = [item for sublist in issues_informational for item in sublist]
        issues_low = [c.detect() for c in checks_low]
        issues_low = [c for c in issues_low if c]
        issues_medium = (c.detect() for c in checks_medium)
        issues_medium = [c for c in issues_medium if c]
        issues_high = [c.detect() for c in checks_high]
        issues_high = [c for c in issues_high if c]
        return (len(issues_informational),
                len(issues_low),
                len(issues_medium),
                len(issues_high))

    def get_detectors_result(self):
        issues_informational, issues_low, issues_medium, issues_high = self._get_detectors_result()
        txt = "Number of informational issues: {}\n".format(green(issues_informational))
        txt += "Number of low issues: {}\n".format(green(issues_low))
        txt += "Number of medium issues: {}\n".format(yellow(issues_medium))
        txt += "Number of high issues: {}\n".format(red(issues_high))

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

    def output(self, _filename):
        """
        _filename is not used
            Args:
                _filename(string)
        """

        txt = "Analyze of {}\n".format(self.slither.filename)
        txt += self.get_detectors_result()
        for contract in self.slither.contracts_derived:
            txt += "\nContract {}\n".format(contract.name)
            txt += self.is_complex_code(contract)
            is_erc20 = contract.is_erc20()
            txt += '\tNumber of functions:{}'.format(self._number_functions(contract))
            txt += "\tIs ERC20 token: {}\n".format(contract.is_erc20())
            if is_erc20:
                txt += self.get_summary_erc20(contract)

        self.info(txt)
