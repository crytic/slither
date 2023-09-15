"""
    Robert "Uncle Bob" Martin - Agile software metrics
    https://en.wikipedia.org/wiki/Software_package_metrics

    Efferent Coupling (Ce): Number of contracts that the contract depends on
    Afferent Coupling (Ca): Number of contracts that depend on a contract
    Instability (I): Ratio of efferent coupling to total coupling (Ce / (Ce + Ca))
    Abstractness (A): Number of abstract contracts / total number of contracts
    Distance from the Main Sequence (D):  abs(A + I - 1)

"""
from typing import Tuple
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.utils.myprettytable import make_pretty_table
from slither.printers.abstract_printer import AbstractPrinter


def count_abstracts(contracts) -> Tuple[int, int]:
    """
    Count the number of abstract contracts
    Args:
        contracts(list): list of contracts
    Returns:
        a tuple of (abstract_contract_count, total_contract_count)
    """
    abstract_contract_count = 0
    for c in contracts:
        if not c.is_fully_implemented:
            abstract_contract_count += 1
    return (abstract_contract_count, len(contracts))


def compute_coupling(contracts: list, abstractness: float) -> dict:
    """
    Used to compute the coupling between contracts external calls made to internal contracts
    Args:
        contracts: list of contracts
    Returns:
        dict of contract names with dicts of the coupling metrics:
        {
        "contract_name1": {
            "Dependents (Ca)": 0,
            "Dependencies (Ce)": 3
            "Instability (I)": 1.0,
            "Abstractness (A)": 0.0,
            "Distance from main sequence (D)": 1.0,
        },
        "contract_name2": {
            "Dependents (Ca)": 1,
            "Dependencies (Ce)": 0
            "Instability (I)": 0.0,
            "Abstractness (A)": 1.0,
            "Distance from main sequence (D)": 0.0,
        }
    """
    dependencies = {}
    for contract in contracts:
        if contract.is_interface:
            continue
        for func in contract.functions:
            high_level_calls = [
                ir for node in func.nodes for ir in node.irs_ssa if isinstance(ir, HighLevelCall)
            ]
            # convert irs to string with target function and contract name
            external_calls = [h.destination.type.type.name for h in high_level_calls]
        dependencies[contract.name] = set(external_calls)
    dependents = {}
    for contract, deps in dependencies.items():
        for dep in deps:
            if dep not in dependents:
                dependents[dep] = set()
            dependents[dep].add(contract)

    coupling_dict = {}
    for contract in contracts:
        ce = len(dependencies.get(contract.name, []))
        ca = len(dependents.get(contract.name, []))
        i = 0.0
        d = 0.0
        if ce + ca > 0:
            i = float(ce / (ce + ca))
            d = float(abs(i - abstractness))
        coupling_dict[contract.name] = {
            "Dependents (Ca)": ca,
            "Dependencies (Ce)": ce,
            "Instability (I)": f"{i:.2f}",
            "Distance from main sequence (D)": f"{d:.2f}",
        }
    return coupling_dict


class Martin(AbstractPrinter):
    ARGUMENT = "martin"
    HELP = "Martin agile software metrics (Ca, Ce, I, A, D)"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#martin"

    def output(self, _filename):
        (abstract_contract_count, total_contract_count) = count_abstracts(self.contracts)
        abstractness = float(abstract_contract_count / total_contract_count)
        coupling_dict = compute_coupling(self.contracts, abstractness)

        table = make_pretty_table(
            ["Contract", *list(coupling_dict[self.contracts[0].name].keys())], coupling_dict
        )
        txt = "Martin agile software metrics\n"
        txt += "Efferent Coupling (Ce) - Number of contracts that a contract depends on\n"
        txt += "Afferent Coupling (Ca) - Number of contracts that depend on the contract\n"
        txt += "Instability (I) - Ratio of efferent coupling to total coupling (Ce / (Ce + Ca))\n"
        txt += "Abstractness (A) - Number of abstract contracts / total number of contracts\n"
        txt += "Distance from the Main Sequence (D) - abs(A + I - 1)\n"
        txt += "\n"
        txt += f"Abstractness (overall): {round(abstractness, 2)}\n" + str(table)
        self.info(txt)
        res = self.generate_output(txt)
        res.add_pretty_table(table, "Code Lines")
        return res
