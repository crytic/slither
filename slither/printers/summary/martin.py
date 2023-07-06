"""
    Robert "Uncle Bob" Martin - Agile software metrics
    https://en.wikipedia.org/wiki/Software_package_metrics

    Efferent Coupling (Ce): Number of contracts that the contract depends on
    Afferent Coupling (Ca): Number of contracts that depend on a contract
    Instability (I): Ratio of efferent coupling to total coupling (Ce / (Ce + Ca))
    Abstractness (A): Number of abstract contracts / total number of contracts
    Distance from the Main Sequence (D):  abs(A + I - 1)

"""
from typing import Tuple, List, Dict
from dataclasses import dataclass, field
from collections import OrderedDict
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.core.declarations import Contract
from slither.utils.myprettytable import make_pretty_table, MyPrettyTable
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
            "Dependents": 0,
            "Dependencies": 3
            "Instability": 1.0,
            "Abstractness": 0.0,
            "Distance from main sequence": 1.0,
        },
        "contract_name2": {
            "Dependents": 1,
            "Dependencies": 0
            "Instability": 0.0,
            "Abstractness": 1.0,
            "Distance from main sequence": 0.0,
        }
    """
    dependencies = {}
    for contract in contracts:
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
            "Dependents": ca,
            "Dependencies": ce,
            "Instability": f"{i:.2f}",
            "Distance from main sequence": f"{d:.2f}",
        }
    return coupling_dict

@dataclass
class MartinContractMetrics:
    contract: Contract
    ca: int
    ce: int
    abstractness: float
    i: float = 0.0
    d: float = 0.0

    def __post_init__(self):
        if self.ce + self.ca > 0:
            self.i = float(self.ce / (self.ce + self.ca))
            self.d = float(abs(self.i - self.abstractness))

    def to_dict(self):
        return {
            "Dependents": self.ca,
            "Dependencies": self.ce,
            "Instability": f"{self.i:.2f}",
            "Distance from main sequence": f"{self.d:.2f}",
        }

@dataclass
class SectionInfo:
    """Class to hold the information for a section of the report."""

    title: str
    pretty_table: MyPrettyTable
    txt: str


@dataclass
class MartinMetrics:
    contracts: List[Contract] = field(default_factory=list)
    abstractness: float = 0.0
    contract_metrics: OrderedDict = field(default_factory=OrderedDict)
    title: str = "Martin complexity metrics"
    full_text: str = ""
    core: SectionInfo = field(default=SectionInfo)
    CORE_KEYS = (
        "Dependents",
        "Dependencies",
        "Instability",
        "Distance from main sequence",
    )
    SECTIONS: Tuple[Tuple[str, Tuple[str]]] = (
        ("Core", CORE_KEYS),
    )

    def __post_init__(self):
        self.update_abstractness()
        self.update_coupling()
        self.update_reporting_sections()

    def update_reporting_sections(self):
        # Create the table and text for each section.
        data = {
            contract.name: self.contract_metrics[contract.name].to_dict()
            for contract in self.contracts
        }
        for (title, keys) in self.SECTIONS:
            pretty_table = make_pretty_table(["Contract", *keys], data, False)
            section_title = f"{self.title} ({title})"
            txt = f"\n\n{section_title}:\n"
            txt = "Martin agile software metrics\n"
            txt += "Efferent Coupling (Ce) - Number of contracts that a contract depends on\n"
            txt += "Afferent Coupling (Ca) - Number of contracts that depend on the contract\n"
            txt += "Instability (I) - Ratio of efferent coupling to total coupling (Ce / (Ce + Ca))\n"
            txt += "Abstractness (A) - Number of abstract contracts / total number of contracts\n"
            txt += "Distance from the Main Sequence (D) - abs(A + I - 1)\n"
            txt += "\n"
            txt += f"Abstractness (overall): {round(self.abstractness, 2)}\n"
            txt += f"{pretty_table}\n"
            self.full_text += txt
            setattr(
                self,
                title.lower(),
                SectionInfo(title=section_title, pretty_table=pretty_table, txt=txt),
            )

    def update_abstractness(self) -> float:
        abstract_contract_count = 0
        for c in self.contracts:
            if not c.is_fully_implemented:
                abstract_contract_count += 1
        self.abstractness = float(abstract_contract_count / len(self.contracts))


    def update_coupling(self) -> Dict:
        dependencies = {}
        for contract in self.contracts:
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
        for contract in self.contracts:
            ce = len(dependencies.get(contract.name, []))
            ca = len(dependents.get(contract.name, []))
            self.contract_metrics[contract.name] = MartinContractMetrics(contract, ca, ce, self.abstractness)


class Martin(AbstractPrinter):
    ARGUMENT = "martin"
    HELP = "Martin agile software metrics (Ca, Ce, I, A, D)"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#martin"

    def output(self, _filename):
        if len(self.contracts) == 0:
            return self.generate_output("No contract found")

        martin = MartinMetrics(self.contracts)

        res = self.generate_output(martin.full_text)
        res.add_pretty_table(martin.core.pretty_table, martin.core.title)
        self.info(martin.full_text)


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
