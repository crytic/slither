"""
    Module printing summary of the contract
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import MyPrettyTable


class Loc(AbstractPrinter):
    ARGUMENT = "loc"
    HELP = "Count the number of lines of code (LOC), source lines of code (SLOC), and comment lines of code (CLOC)"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#dominator"  # TODO

    def output(self, _filename):
        sloc = self.slither.code_lines["sloc"]
        loc = self.slither.code_lines["loc"]
        cloc = self.slither.code_lines["cloc"]
        table = MyPrettyTable(["Type", "Amount"])
        table.add_row(["LOC", loc])
        table.add_row(["SLOC", sloc])
        table.add_row(["CLOC", cloc])
        txt = "Lines of Code \n" + str(table)
        self.info(txt)
        res = self.generate_output(txt)
        res.add_pretty_table(table, "Code Lines")
        return res
