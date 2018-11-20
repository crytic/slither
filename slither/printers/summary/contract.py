"""
    Module printing summary of the contract
"""
import collections
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.colors import blue, green, magenta

class ContractSummary(AbstractPrinter):

    ARGUMENT = 'contract-summary'
    HELP = 'Print a summary of the contracts'

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
            # (c_name, f_name, visi, _, _, _, _, _) in func_summaries
            public = [(elem[0], (elem[1], elem[2]) ) for elem in func_summaries]

            collect = collections.defaultdict(list)
            for a,b in public:
                collect[a].append(b)
            public = list(collect.items())

            for contract, functions in public:
                txt += blue("  - From {}\n".format(contract))
                functions = sorted(functions)
                for (function, visi) in functions:
                    if visi in ['external', 'public']:
                        txt += green("    - {} ({})\n".format(function, visi))
                for (function, visi) in functions:
                    if visi in ['internal', 'private']:
                        txt += magenta("    - {} ({})\n".format(function, visi))
                for (function, visi) in functions:
                    if visi not in ['external', 'public', 'internal', 'private']:
                        txt += "    - {}  ({})\n".format(function, visi)

        self.info(txt)
