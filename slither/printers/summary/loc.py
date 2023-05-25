"""
    Lines of Code (LOC) printer

    Definitions:
    cloc: comment lines of code containing only comments
    sloc: source lines of code with no whitespace or comments
    loc: all lines of code including whitespace and comments
    src: source files (excluding tests and dependencies)
    dep: dependency files
    test: test files
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.loc import compute_loc_metrics
from slither.utils.output import Output


class LocPrinter(AbstractPrinter):
    ARGUMENT = "loc"
    HELP = """Count the total number lines of code (LOC), source lines of code (SLOC), \
            and comment lines of code (CLOC) found in source files (SRC), dependencies (DEP), \
            and test files (TEST)."""

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#loc"

    def output(self, _filename: str) -> Output:
        # compute loc metrics
        loc = compute_loc_metrics(self.slither)

        table = loc.to_pretty_table()
        txt = "Lines of Code \n" + str(table)
        self.info(txt)
        res = self.generate_output(txt)
        res.add_pretty_table(table, "Code Lines")
        return res
