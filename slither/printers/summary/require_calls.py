"""
    Module printing summary of the contract
"""

from prettytable import PrettyTable
from slither.core.declarations import SolidityFunction
from slither.printers.abstract_printer import AbstractPrinter
from slither.slithir.operations import SolidityCall

require_or_assert = [SolidityFunction("assert(bool)"),
                     SolidityFunction("require(bool)"),
                     SolidityFunction("require(bool,string)")]

class RequireOrAssert(AbstractPrinter):

    ARGUMENT = 'require'
    HELP = 'Print the require and assert calls of each function'

    WIKI = 'https://github.com/trailofbits/slither/wiki/Printer-documentation#require'

    @staticmethod
    def _convert(l):
        return "\n".join(l)

    def output(self, _filename):
        """
            _filename is not used
            Args:
                _filename(string)
        """

        for contract in self.slither.contracts_derived:
            txt = "\nContract %s"%contract.name
            table = PrettyTable(["Function",
                                 "require or assert"])
            for function in contract.functions:
                require = function.all_slithir_operations()
                require = [ir for ir in require if isinstance(ir, SolidityCall) and ir.function in require_or_assert]
                require = [ir.node for ir in require]
                table.add_row([function.name, self._convert([str(m.expression) for m in set(require)])])
            txt += "\n"+str(table)
            self.info(txt)
