"""
    Module printing summary of the contract
"""
import collections
from prettytable import PrettyTable
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.colors import blue, green, magenta
from slither.utils.function import get_function_id

class FunctionIds(AbstractPrinter):

    ARGUMENT = 'function-id'
    HELP = 'Print the keccack256 signature of the functions'

    WIKI = 'https://github.com/trailofbits/slither/wiki/Printer-documentation#function-id'

    def output(self, _filename):
        """
            _filename is not used
            Args:
                _filename(string)
        """

        txt = ''
        for contract in self.slither.contracts_derived:
            txt += '\n{}:\n'.format(contract.name)
            table = PrettyTable(['Name', 'ID'])
            for function in contract.functions:
                if function.visibility in ['public', 'external']:
                    table.add_row([function.full_name, hex(get_function_id(function.full_name))])
            for variable in contract.state_variables:
                if variable.visibility in ['public']:
                    table.add_row([variable.name+'()', hex(get_function_id(variable.name+'()'))])
            txt += str(table) + '\n'

        self.info(txt)
