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

        all_contracts = []
        for c in self.contracts:
            txt += blue("\n+ Contract %s\n" % c.name)
            additional_fields = {"elements": []}

            # Order the function with
            # contract_declarer -> list_functions
            public = [(f.contract_declarer.name, f) for f in c.functions if (not f.is_shadowed)]
            collect = collections.defaultdict(list)
            for a, b in public:
                collect[a].append(b)
            public = list(collect.items())

            for contract, functions in public:
                txt += blue("  - From {}\n".format(contract))

                functions = sorted(functions, key=lambda f: f.full_name)

                for function in functions:
                    if function.visibility in ['external', 'public']:
                        txt += green("    - {} ({})\n".format(function, function.visibility))
                    if function.visibility in ['internal', 'private']:
                        txt += magenta("    - {} ({})\n".format(function, function.visibility))
                    if function.visibility not in ['external', 'public', 'internal', 'private']:
                        txt += "    - {}  ({})\n".format(function, function.visibility)

                    self.add_function_to_json(function, additional_fields, additional_fields={"visibility":
                                                                                              function.visibility})

            all_contracts.append((c, additional_fields))

        self.info(txt)

        json = self.generate_json_result(txt)
        for contract, additional_fields in all_contracts:
            self.add_contract_to_json(contract, json, additional_fields=additional_fields)

        return json
