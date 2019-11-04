"""
    Module printing summary of the contract
"""

from prettytable import PrettyTable
from slither.core.declarations import Function
from slither.printers.abstract_printer import AbstractPrinter


class Modifiers(AbstractPrinter):

    ARGUMENT = 'modifiers'
    HELP = 'Print the modifiers called by each function'

    WIKI = 'https://github.com/trailofbits/slither/wiki/Printer-documentation#modifiers'

    def output(self, _filename):
        """
            _filename is not used
            Args:
                _filename(string)
        """

        all_txt = ''
        all_tables = []

        for contract in self.slither.contracts_derived:
            txt = "\nContract %s"%contract.name
            table = PrettyTable(["Function",
                                 "Modifiers"])
            for function in contract.functions:
                modifiers = function.modifiers
                for call in function.all_internal_calls():
                    if isinstance(call, Function):
                        modifiers += call.modifiers
                for (_, call) in function.all_library_calls():
                    if isinstance(call, Function):
                        modifiers += call.modifiers
                table.add_row([function.name, [m.name for m in set(modifiers)]])
            txt += "\n"+str(table)
            self.info(txt)

        json = self.generate_json_result(all_txt)
        for name, table in all_tables:
            self.add_pretty_table_to_json(table, name, json)

        return json