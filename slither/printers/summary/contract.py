"""
    Module printing summary of the contract
"""
import collections
from typing import Dict, List

from slither.core.declarations import FunctionContract
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils import output
from slither.utils.colors import blue, green, magenta
from slither.utils.output import Output


class ContractSummary(AbstractPrinter):
    ARGUMENT = "contract-summary"
    HELP = "Print a summary of the contracts"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#contract-summary"

    def output(self, _filename: str) -> Output:  # pylint: disable=too-many-locals
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

            additional_txt_info = ""

            if is_upgradeable_proxy:
                additional_txt_info += " (Upgradeable Proxy)"

            if is_upgradeable:
                additional_txt_info += " (Upgradeable)"

            if c in self.slither.contracts_derived:
                additional_txt_info += " (Most derived contract)"

            txt += blue(f"\n+ Contract {c.name}{additional_txt_info}\n")
            additional_fields = output.Output(
                "",
                additional_fields={
                    "is_upgradeable_proxy": is_upgradeable_proxy,
                    "is_upgradeable": is_upgradeable,
                    "is_most_derived": c in self.slither.contracts_derived,
                },
            )

            # Order the function with
            # contract_declarer -> list_functions
            public_function = [
                (f.contract_declarer.name, f)
                for f in c.functions
                if (not f.is_shadowed and not f.is_constructor_variables)
            ]
            collect: Dict[str, List[FunctionContract]] = collections.defaultdict(list)
            for a, b in public_function:
                collect[a].append(b)

            for contract, functions in collect.items():
                txt += blue(f"  - From {contract}\n")

                functions = sorted(functions, key=lambda f: f.full_name)

                for function in functions:
                    if function.visibility in ["external", "public"]:
                        txt += green(f"    - {function.full_name} ({function.visibility})\n")
                    if function.visibility in ["internal", "private"]:
                        txt += magenta(f"    - {function.full_name} ({function.visibility})\n")
                    if function.visibility not in [
                        "external",
                        "public",
                        "internal",
                        "private",
                    ]:
                        txt += f"    - {function.full_name}  ({function.visibility})\n"

                    additional_fields.add(
                        function, additional_fields={"visibility": function.visibility}
                    )

            all_contracts.append((c, additional_fields.data))

        self.info(txt)

        res = self.generate_output(txt)
        for current_contract, current_additional_fields in all_contracts:
            res.add(current_contract, additional_fields=current_additional_fields)

        return res
