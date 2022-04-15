"""
    Module printing summary of the contract
"""

from slither.core.declarations import Function
from slither.core.declarations.function import SolidityFunction
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils import output
from slither.utils.myprettytable import MyPrettyTable


def _use_modifier(function: Function, modifier_name: str = "whenNotPaused") -> bool:
    if function.is_constructor or function.view or function.pure:
        return False

    for internal_call in function.all_internal_calls():
        if isinstance(internal_call, SolidityFunction):
            continue
        if any(modifier.name == modifier_name for modifier in function.modifiers):
            return True
    return False


class PrinterWhenNotPaused(AbstractPrinter):

    ARGUMENT = "pausable"
    HELP = "Print functions that do not use whenNotPaused"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#when-not-paused"

    def output(self, _filename: str) -> output.Output:
        """
        _filename is not used
        Args:
            _filename(string)
        """

        modifier_name: str = "whenNotPaused"

        txt = ""
        txt += "Constructor and pure/view functions are not displayed\n"
        all_tables = []
        for contract in self.slither.contracts:

            txt += f"\n{contract.name}:\n"
            table = MyPrettyTable(["Name", "Use whenNotPaused"])

            for function in contract.functions_entry_points:
                status = "X" if _use_modifier(function, modifier_name) else ""
                table.add_row([function.solidity_signature, status])

            txt += str(table) + "\n"
            all_tables.append((contract.name, table))

        self.info(txt)

        res = self.generate_output(txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res
