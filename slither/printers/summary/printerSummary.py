"""
    Module printing summary of the contract
"""

from prettytable import PrettyTable
from slither.printers.abstract_printer import AbstractPrinter

class PrinterSummary(AbstractPrinter):

    ARGUMENT = 'summary'
    HELP = 'the summary of the contract'

    @staticmethod
    def _convert(l):
        if l:
            n = 2
            l = [l[i:i + n] for i in range(0, len(l), n)]
            l = [str(x) for x in l]
            return "\n".join(l)
        return str(l)

    def output(self, _filename):
        """
            _filename is not used
            Args:
                _filename(string)
        """

        for c in self.contracts:
            (name, var, inheritances, func_summaries, modif_summaries) = c.get_summary()
            txt = "\nContract %s"%name
            txt += '\nContract vars: '+str(var)
            txt += '\nInheritances:: '+str(inheritances)
            table = PrettyTable(["Function", "Visibility", "Modifiers", "Read", "Write", "Calls"])
            for (f_name, visi, modifiers, read, write, calls) in func_summaries:
                read = self._convert(read)
                write = self._convert(write)
                calls = self._convert(calls)
                table.add_row([f_name, visi, modifiers, read, write, calls])
            txt += "\n \n"+str(table)
            table = PrettyTable(["Modifiers", "Visibility", "Read", "Write", "Calls"])
            for (f_name, visi, _, read, write, calls) in modif_summaries:
                read = self._convert(read)
                write = self._convert(write)
                calls = self._convert(calls)
                table.add_row([f_name, visi, read, write, calls])
            txt += "\n\n"+str(table)
            txt += "\n"
            self.info(txt)
