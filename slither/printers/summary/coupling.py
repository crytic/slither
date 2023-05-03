"""
    Coupling metrics printer

    Efferent Coupling (Ce) - Number of contracts that the contract depends on
    Afferent Coupling (Ca) - Number of contracts that depend on a contract

"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import make_pretty_table


def compute_coupling(contracts: list) -> dict:
    """Used to compute the coupling between contracts based on inheritance
    Args:
        contracts: list of contracts
    Returns:
        dict of contract names with dicts of the coupling metrics:
        {
        "contract_name1": {"dependents_Ca": 0, "dependencies_Ce": 3},
        "contract_name2": {"dependents_Ca": 2, "dependencies_Ce": 1},
        }
    """

    ca_table = {
        inherited.name: {
            contract.name for contract in contracts if inherited.name in contract.inheritance
        }
        for inherited in contracts
    }

    coupling_dict = {}
    for contract in contracts:
        ce = len(contract.inheritance)
        ca = len(ca_table.get(contract.name, []))
        coupling_dict[contract.name] = {"dependents_Ca": ca, "dependencies_Ce": ce}
    return coupling_dict


class Coupling(AbstractPrinter):
    ARGUMENT = "coupling"
    HELP = "Measures the coupling between contracts based on inheritance"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#coupling"

    def output(self, _filename):
        coupling_dict = compute_coupling(self.contracts)

        table = make_pretty_table(
            ["Contract", *list(coupling_dict[self.contracts[0].name].keys())], coupling_dict
        )
        txt = "Coupling\nEfferent Coupling (Ce) - Number of contracts that "
        txt += "a contract depends on\nAfferent Coupling (Ca) - Number of "
        txt += "contracts that depend on the contract\n" + str(table)
        self.info(txt)
        res = self.generate_output(txt)
        res.add_pretty_table(table, "Code Lines")
        return res
