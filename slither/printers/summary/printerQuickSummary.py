"""
    Module printing summary of the contract
"""

from slither.printers.abstractPrinter import AbstractPrinter
from slither.utils.colors import blue, green, magenta

class PrinterQuickSummary(AbstractPrinter):

    ARGUMENT = 'quick-summary'
    HELP = 'a quick summary of the contract'

    def output(self, _filename):
        """
            _filename is not used
            Args:
                _filename(string)
        """

        txt = ""
        for c in self.contracts:
            (name, var, func_summaries, modif_summaries) = c.get_summary()
            txt += blue("\n+ Contract %s\n"%name)
            for (f_name, visi, modifiers, read, write, calls) in func_summaries:
                txt += "  - "
                if visi in ['external', 'public']:
                    txt += green("%s (%s)\n"%(f_name, visi))
                elif visi in ['internal','private']:
                    txt += magenta("%s (%s)\n"%(f_name, visi))
                else:
                    txt += "%s (%s)\n"%(f_name, visi)
        self.info(txt)
