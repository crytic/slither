"""
    Module printing summary of the contract
"""

from prettytable import PrettyTable
from slither.printers.abstract_printer import AbstractPrinter

class VariablesOrder(AbstractPrinter):

    ARGUMENT = 'variables-order'
    HELP = 'Print the storage order of the state variables'

    def output(self, _filename):
        """
            _filename is not used
            Args:
                _filename(string)
        """

        txt = ''
        for contract in self.slither.contracts_derived:
            txt += '\n{}:\n'.format(contract.name)
            table = PrettyTable(['Name', 'Type'])
            for variable in contract.state_variables:
                if not variable.is_constant:
                    table.add_row([variable.name, str(variable.type)])
            txt += str(table) + '\n'

        self.info(txt)
