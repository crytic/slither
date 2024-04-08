"""
    Cheatcode printer

    This printer prints the usage of cheatcode in the code.
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils import output


class CheatcodePrinter(AbstractPrinter):

    ARGUMENT = "cheatcode"

    HELP = """"""

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#cheatcode"

    def output(self, filename: str) -> output.Output:
        pass
