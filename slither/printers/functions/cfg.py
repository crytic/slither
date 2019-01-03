"""
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.core.declarations.function import Function

class CFG(AbstractPrinter):

    ARGUMENT = 'cfg'
    HELP = 'Export the CFG of each functions'

    def output(self, original_filename):
        """
            _filename is not used
            Args:
                _filename(string)
        """

        for contract in self.contracts:
            for function in contract.functions + contract.modifiers:
                filename = "{}-{}-{}.dot".format(original_filename, contract.name, function.full_name)
                self.info('Export {}'.format(filename))
                function.slithir_cfg_to_dot(filename)

