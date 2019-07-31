"""
    Module printing summary of the contract
"""
import collections
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.colors import blue, green, magenta

class ContractSummary(AbstractPrinter):

    ARGUMENT = 'contract-summary'
    HELP = 'Print a summary of the contracts'

    WIKI = 'https://github.com/trailofbits/slither/wiki/Printer-documentation#contract-summary'

    def output(self, _filename):
        """
            _filename is not used
            Args:
                _filename(string)
        """

        txt = ""
        json_result = {}
        for c in self.contracts:
            (name, _inheritance, _var, func_summaries, _modif_summaries) = c.get_summary()
            txt += blue("\n+ Contract %s\n"%name)
            json_result[name] = {}
            # (c_name, f_name, visi, _, _, _, _, _) in func_summaries
            public = [(elem[0], (elem[1], elem[2]) ) for elem in func_summaries]

            collect = collections.defaultdict(list)
            for a,b in public:
                collect[a].append(b)
            public = list(collect.items())

            for contract, functions in public:
                txt += blue("  - From {}\n".format(contract))
                json_result[name]['from'] = str(contract)
                functions = sorted(functions)
                json_result[name]['functions'] = {}
                json_result[name]['functions']['visible'] = []
                json_result[name]['functions']['invisible'] = []
                json_result[name]['functions']['others'] = []
                for (function, visi) in functions:
                    if visi in ['external', 'public']:
                        json_result[name]['functions']['visible'].append({'function':function,'visi':visi})
                        txt += green("    - {} ({})\n".format(function, visi))
                for (function, visi) in functions:
                    if visi in ['internal', 'private']:
                        json_result[name]['functions']['invisible'].append({'function':function,'visi':visi})
                        txt += magenta("    - {} ({})\n".format(function, visi))
                for (function, visi) in functions:
                    if visi not in ['external', 'public', 'internal', 'private']:
                        json_result[name]['functions']['others'].append({'function':function,'visi':visi})
                        txt += "    - {}  ({})\n".format(function, visi)

        self.info(txt)
        return json_result