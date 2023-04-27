"""
    Module printing summary of the contract
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import MyPrettyTable


# Converts a dict to a MyPrettyTable.  Dict keys are the contract names.
# @param takes a str[] of headers
# @param takes a dict of contract names with a tuple of the values
def make_pretty_table(headers: list, body: dict) -> MyPrettyTable:
    table = MyPrettyTable(headers)
    for key, value in body.items():
        table.add_row([key, value[0], value[1]])
    return table


# Efferent Coupling (Ce) - Number of contracts that the contract depends on
# Afferent Coupling (Ca) - Number of contracts that depend on a contract
# @param takes a list of contract objects
# @param returns a dict of contract names with a tuple of the Ce and Ca values:
# {
#   "contract_name1": (Ce: int, Ca: int),
#   "contract_name2": (Ce: int, Ca: int),
# }
def compute_coupling(contracts: list) -> dict:
    # -> Ce is the length of the .inherited list for each contract
    # -> Ca is the number of times a contract is inherited by another contract
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
        coupling_dict[contract.name] = (ce, ca)
    return coupling_dict


class Coupling(AbstractPrinter):
    ARGUMENT = "coupling"
    HELP = "?"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#dominator"  # TODO

    def output(self, _filename):
        coupling_dict = compute_coupling(self.contracts)
        table = make_pretty_table(["Contract", "Ce", "Ca"], coupling_dict)
        txt = "Coupling\nEfferent Coupling (Ce) - Number of contracts that "
        txt += "a contract depends on\nAfferent Coupling (Ca) - Number of "
        txt += "contracts that depend on the contract\n" + str(table)
        self.info(txt)
        res = self.generate_output(txt)
        res.add_pretty_table(table, "Code Lines")
        return res
