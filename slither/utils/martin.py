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


@dataclass
class MartinContractMetrics:
    contract: Contract
    ca: int
    ce: int
    abstractness: float
    i: float = 0.0
    d: float = 0.0

    def __post_init__(self) -> None:
        if self.ce + self.ca > 0:
            self.i = float(self.ce / (self.ce + self.ca))
            self.d = float(abs(self.i - self.abstractness))

    def to_dict(self) -> Dict:
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
    SECTIONS: Tuple[Tuple[str, str, Tuple[str]]] = (("Core", "core", CORE_KEYS),)

    def __post_init__(self) -> None:
        self.update_abstractness()
        self.update_coupling()
        self.update_reporting_sections()

    def update_reporting_sections(self) -> None:
        # Create the table and text for each section.
        data = {
            contract.name: self.contract_metrics[contract.name].to_dict()
            for contract in self.contracts
        }
        for (title, attr, keys) in self.SECTIONS:
            pretty_table = make_pretty_table(["Contract", *keys], data, False)
            section_title = f"{self.title} ({title})"
            txt = f"\n\n{section_title}:\n"
            txt = "Martin agile software metrics\n"
            txt += "Efferent Coupling (Ce) - Number of contracts that a contract depends on\n"
            txt += "Afferent Coupling (Ca) - Number of contracts that depend on the contract\n"
            txt += (
                "Instability (I) - Ratio of efferent coupling to total coupling (Ce / (Ce + Ca))\n"
            )
            txt += "Abstractness (A) - Number of abstract contracts / total number of contracts\n"
            txt += "Distance from the Main Sequence (D) - abs(A + I - 1)\n"
            txt += "\n"
            txt += f"Abstractness (overall): {round(self.abstractness, 2)}\n"
            txt += f"{pretty_table}\n"
            self.full_text += txt
            setattr(
                self,
                attr,
                SectionInfo(title=section_title, pretty_table=pretty_table, txt=txt),
            )

    def update_abstractness(self) -> None:
        abstract_contract_count = 0
        for c in self.contracts:
            if not c.is_fully_implemented:
                abstract_contract_count += 1
        self.abstractness = float(abstract_contract_count / len(self.contracts))

    # pylint: disable=too-many-branches
    def update_coupling(self) -> None:
        dependencies = {}
        for contract in self.contracts:
            external_calls = []
            for func in contract.functions:
                high_level_calls = [
                    ir
                    for node in func.nodes
                    for ir in node.irs_ssa
                    if isinstance(ir, HighLevelCall)
                ]
                # convert irs to string with target function and contract name
                # Get the target contract name for each high level call
                new_external_calls = []
                for high_level_call in high_level_calls:
                    if isinstance(high_level_call.destination, Contract):
                        new_external_call = high_level_call.destination.name
                    elif isinstance(high_level_call.destination, str):
                        new_external_call = high_level_call.destination
                    elif not hasattr(high_level_call.destination, "type"):
                        continue
                    elif isinstance(high_level_call.destination.type, Contract):
                        new_external_call = high_level_call.destination.type.name
                    elif isinstance(high_level_call.destination.type, str):
                        new_external_call = high_level_call.destination.type
                    elif not hasattr(high_level_call.destination.type, "type"):
                        continue
                    elif isinstance(high_level_call.destination.type.type, Contract):
                        new_external_call = high_level_call.destination.type.type.name
                    elif isinstance(high_level_call.destination.type.type, str):
                        new_external_call = high_level_call.destination.type.type
                    else:
                        continue
                    new_external_calls.append(new_external_call)
                external_calls.extend(new_external_calls)
            dependencies[contract.name] = set(external_calls)
        dependents = {}
        for contract, deps in dependencies.items():
            for dep in deps:
                if dep not in dependents:
                    dependents[dep] = set()
                dependents[dep].add(contract)

        for contract in self.contracts:
            ce = len(dependencies.get(contract.name, []))
            ca = len(dependents.get(contract.name, []))
            self.contract_metrics[contract.name] = MartinContractMetrics(
                contract, ca, ce, self.abstractness
            )
