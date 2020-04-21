"""
    Module printing summary of the contract
"""
from prettytable import PrettyTable

from slither.printers.abstract_printer import AbstractPrinter
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
        all_tables = []
        for contract in self.slither.contracts_derived:
            txt += '\n{}:\n'.format(contract.name)
            table = PrettyTable(['Name', 'ID'])
            for function in contract.functions:
                if function.visibility in ['public', 'external']:
                    table.add_row([function.solidity_signature, hex(get_function_id(function.solidity_signature))])
            for variable in contract.state_variables:
                if variable.visibility in ['public']:
                    sig = variable.function_name
                    table.add_row([sig, hex(get_function_id(sig))])
            txt += str(table) + '\n'
            all_tables.append((contract.name, table))

        self.info(txt)

        res = self.generate_output(txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res