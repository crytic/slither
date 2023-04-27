"""
    Module printing summary of the contract
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.colors import blue, green
from typing import Tuple


def count_abstracts(contracts) -> Tuple[int, int]:
    total_contract_count = 0
    abstract_contract_count = 0
    for c in contracts:
        total_contract_count += 1
        if not c.is_fully_implemented:
            abstract_contract_count += 1
    return (abstract_contract_count, total_contract_count)


class Abstractness(AbstractPrinter):
    ARGUMENT = "abstractness"
    HELP = "Number of abstract contracts / total number of contracts"

    WIKI = (
        "https://github.com/trailofbits/slither/wiki/Printer-documentation#contract-summary"  # TODO
    )

    def output(self, _filename):
        """
        _filename is not used
        Args:
            _filename(string)
        """
        (abstract_contract_count, total_contract_count) = count_abstracts(self.contracts)
        abstractness = 1.0 * abstract_contract_count / total_contract_count
        abstractness_formatted = "{:.2f}".format(abstractness)  # is there a more modern way to do this?

        txt = f"\nAbstract contracts {blue(abstract_contract_count)}\n"
        txt += f"Total contracts {green(total_contract_count)}\n"
        txt += f"Abstractness: {abstractness_formatted}\n"
        self.info(txt)
        res = self.generate_output(txt)

        return res
