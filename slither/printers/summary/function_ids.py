"""
    Module printing summary of the contract
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.function import get_function_id
from slither.utils.myprettytable import MyPrettyTable


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
            table = MyPrettyTable(['Solidity Signature', 'ID', 'Return types'])
            for function in contract.functions:
                if function.visibility in ['public', 'external']:
                    _, _, returns = function.signature
                    table.add_row([function.solidity_signature,
                                   hex(get_function_id(function.solidity_signature)),
                                   ','.join(returns)])
            for variable in contract.state_variables:
                if variable.visibility in ['public']:
                    _, _, returns = variable.signature
                    table.add_row([variable.solidity_signature,
                                   hex(get_function_id(variable.solidity_signature)),
                                   ','.join(returns)])
            txt += str(table) + '\n'
            all_tables.append((contract.name, table))

        self.info(txt)

        res = self.generate_output(txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res