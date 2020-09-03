"""
    Module printing summary of the contract
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import MyPrettyTable


class VariableOrder(AbstractPrinter):

    ARGUMENT = "variable-order"
    HELP = "Print the storage order of the state variables"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#variable-order"

    def output(self, _filename):
        """
        _filename is not used
        Args:
            _filename(string)
        """

        txt = ""

        all_tables = []

        for contract in self.slither.contracts_derived:
            txt += "\n{}:\n".format(contract.name)
            table = MyPrettyTable(["Name", "Type", "Slot", "Offset"])
            for variable in contract.state_variables_ordered:
                if not variable.is_constant:
                    slot, offset = self.slither.storage_layout_of(contract, variable)
                    table.add_row([variable.canonical_name, str(variable.type), slot, offset])

            all_tables.append((contract.name, table))
            txt += str(table) + "\n"

        self.info(txt)

        res = self.generate_output(txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)
        return res
