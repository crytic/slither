"""
    Module printing summary of the contract
"""
import collections
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils import output
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

            is_upgradeable_proxy = c.is_upgradeable_proxy
            is_upgradeable = c.is_upgradeable

            additional_txt_info = ''

            if is_upgradeable_proxy:
                additional_txt_info += ' (Upgradeable Proxy)'

            if is_upgradeable:
                additional_txt_info += ' (Upgradeable)'

            if c in self.slither.contracts_derived:
                additional_txt_info += ' (Most derived contract)'

            txt += blue(f"\n+ Contract {c.name}{additional_txt_info}\n")
            additional_fields = output.Output('', additional_fields={
                'is_upgradeable_proxy': is_upgradeable_proxy,
                'is_upgradeable': is_upgradeable,
                'is_most_derived': c in self.slither.contracts_derived
            })

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

                    additional_fields.add(function, additional_fields={"visibility":
                                                                       function.visibility,})

            all_contracts.append((c, additional_fields.data))

        self.info(txt)

        res = self.generate_output(txt)
        for contract, additional_fields in all_contracts:
            res.add(contract, additional_fields=additional_fields)

        return res
