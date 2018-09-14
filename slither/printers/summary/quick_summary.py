"""
    Module printing summary of the contract
"""

from slither.printers.abstract_printer import AbstractPrinter
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
            (name, _inheritance, _var, func_summaries, _modif_summaries) = c.get_summary()
            txt += blue("\n+ Contract %s\n"%name)
            for (f_name, visi, _, _, _, _, _) in func_summaries:
                txt += "  - "
                if visi in ['external', 'public']:
                    txt += green("%s (%s)\n"%(f_name, visi))
                elif visi in ['internal', 'private']:
                    txt += magenta("%s (%s)\n"%(f_name, visi))
                else:
                    txt += "%s (%s)\n"%(f_name, visi)
        self.info(txt)
