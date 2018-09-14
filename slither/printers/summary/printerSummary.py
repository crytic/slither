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
            (name, inheritance, var, func_summaries, modif_summaries) = c.get_summary()
            txt = "\nContract %s"%name
            txt += '\nContract vars: '+str(var)
            txt += '\nInheritance:: '+str(inheritance)
            table = PrettyTable(["Function",
                                 "Visibility",
                                 "Modifiers",
                                 "Read",
                                 "Write",
                                 "Internal Calls",
                                 "External Calls"])
            for (f_name, visi, modifiers, read, write, internal_calls, external_calls) in func_summaries:
                read = self._convert(read)
                write = self._convert(write)
                internal_calls = self._convert(internal_calls)
                external_calls = self._convert(external_calls)
                table.add_row([f_name, visi, modifiers, read, write, internal_calls, external_calls])
            txt += "\n \n"+str(table)
            table = PrettyTable(["Modifiers",
                                 "Visibility",
                                 "Read",
                                 "Write",
                                 "Internal Calls",
                                 "External Calls"])
            for (f_name, visi, _, read, write, internal_calls, external_calls) in modif_summaries:
                read = self._convert(read)
                write = self._convert(write)
                internal_calls = self._convert(internal_calls)
                external_calls = self._convert(external_calls)
                table.add_row([f_name, visi, read, write, internal_calls, external_calls])
            txt += "\n\n"+str(table)
            txt += "\n"
            self.info(txt)
