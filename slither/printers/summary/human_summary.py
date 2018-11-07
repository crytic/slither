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
    def get_summary_erc20(contract):
        txt = ''
        functions_name = [f.name for f in contract.functions]
        state_variables = [v.name for v in contract.state_variables]

        if 'pause' in functions_name:
            txt += "\t\t Can be paused? : {}\n".format(yellow('Yes'))
        else:
            txt += "\t\t Can be paused? : {}\n".format(green('No'))

        if 'mint' in functions_name:
            if not 'mintingFinished' in state_variables:
                txt += "\t\t Minting restriction? : {}\n".format(red('None'))
            else:
                txt += "\t\t Minting restriction? : {}\n".format(yellow('Yes'))
        else:
            txt += "\t\t Minting restriction? : {}\n".format(green('No Minting'))

        if 'increaseApproval' in functions_name or 'safeIncreaseAllowance' in functions_name:
            txt += "\t\t ERC20 race condition mitigation: {}\n".format(green('Yes'))
        else:
            txt += "\t\t ERC20 race condition mitigation: {}\n".format(red('No'))

        return txt

    def get_detectors_result(self):

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

        txt = "Number of informational issues: {}\n".format(green(len(issues_informational)))
        txt += "Number of low issues: {}\n".format(green(len(issues_low)))
        txt += "Number of medium issues: {}\n".format(yellow(len(issues_medium)))
        txt += "Number of high issues: {}\n".format(red(len(issues_high)))

        return txt

    @staticmethod
    def is_complex_code(contract):
        """
            Check if the code is complex
            Heuristic, the code is complex if:
                - One function has a cyclomatic complexity > 7
        Args:
            contract
        """
        is_complex = False

        for f in contract.functions:
            if compute_cyclomatic_complexity(f) > 7:
                is_complex = True

        result = red('Yes') if is_complex else green('No')

        return "\tComplex code? {}\n".format(result)

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
            txt += '\tNumber of functions:{}'.format(len(contract.functions))
            txt += "\tIs ERC20 token: {}\n".format(contract.is_erc20())
            if is_erc20:
                txt += self.get_summary_erc20(contract)

        self.info(txt)
