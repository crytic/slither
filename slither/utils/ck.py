"""
Description

"""
import math
from dataclasses import dataclass, field
from typing import Tuple, List, Dict
from collections import OrderedDict
from slither.core.declarations import Contract
from slither.slithir.variables.temporary import TemporaryVariable
from slither.utils.myprettytable import make_pretty_table, MyPrettyTable
from slither.utils.upgradeability import encode_ir_for_halstead


@dataclass
# pylint: disable=too-many-instance-attributes
class TEMPLATEContractMetrics:
    """Class to hold the TEMPLATE metrics for a single contract."""

    contract: Contract

    def __post_init__(self):
        # """Operators and operands can be passed in as constructor args to avoid computing
        # them based on the contract. Useful for computing metrics for ALL_CONTRACTS"""
        # if len(self.all_operators) == 0:
        #     self.populate_operators_and_operands()
        # if len(self.all_operators) > 0:
        #     self.compute_metrics()
        pass

    def to_dict(self) -> Dict[str, float]:
        """Return the metrics as a dictionary."""
        return OrderedDict(
            # {
            #     "Total Operators": self.N1,
            #     "Unique Operators": self.n1,
            #     "Total Operands": self.N2,
            #     "Unique Operands": self.n2,
            #     "Vocabulary": str(self.n1 + self.n2),
            #     "Program Length": str(self.N1 + self.N2),
            #     "Estimated Length": f"{self.S:.0f}",
            #     "Volume": f"{self.V:.0f}",
            #     "Difficulty": f"{self.D:.0f}",
            #     "Effort": f"{self.E:.0f}",
            #     "Time": f"{self.T:.0f}",
            #     "Estimated Bugs": f"{self.B:.3f}",
            # }
        )

    def compute_metrics(self):
        # """Compute the Halstead metrics."""
        # if all_operators is None:
        #     all_operators = self.all_operators
        #     all_operands = self.all_operands

        # # core metrics
        # self.n1 = len(set(all_operators))
        # self.n2 = len(set(all_operands))
        # self.N1 = len(all_operators)
        # self.N2 = len(all_operands)
        # if any(number <= 0 for number in [self.n1, self.n2, self.N1, self.N2]):
        #     raise ValueError("n1 and n2 must be greater than 0")

        # # extended metrics 1
        # self.n = self.n1 + self.n2
        # self.N = self.N1 + self.N2
        # self.S = self.n1 * math.log2(self.n1) + self.n2 * math.log2(self.n2)
        # self.V = self.N * math.log2(self.n)

        # # extended metrics 2
        # self.D = (self.n1 / 2) * (self.N2 / self.n2)
        # self.E = self.D * self.V
        # self.T = self.E / 18
        # self.B = (self.E ** (2 / 3)) / 3000
        pass


@dataclass
class SectionInfo:
    """Class to hold the information for a section of the report."""

    title: str
    pretty_table: MyPrettyTable
    txt: str


@dataclass
# pylint: disable=too-many-instance-attributes
class TEMPLATEMetrics:
    """Class to hold the TEMPLATE metrics for all contracts. Contains methods useful for reporting.

    There are 3 sections in the report:
    1. Core metrics (n1, n2, N1, N2)
    2. Extended metrics 1 (n, N, S, V)
    3. Extended metrics 2 (D, E, T, B)

    """

    contracts: List[Contract] = field(default_factory=list)
    contract_metrics: OrderedDict = field(default_factory=OrderedDict)
    title: str = "Halstead complexity metrics"
    full_txt: str = ""
    # core: SectionInfo = field(default=SectionInfo)
    # extended1: SectionInfo = field(default=SectionInfo)
    # extended2: SectionInfo = field(default=SectionInfo)
    # CORE_KEYS = (
    #     "Total Operators",
    #     "Unique Operators",
    #     "Total Operands",
    #     "Unique Operands",
    # )
    # EXTENDED1_KEYS = (
    #     "Vocabulary",
    #     "Program Length",
    #     "Estimated Length",
    #     "Volume",
    # )
    # EXTENDED2_KEYS = (
    #     "Difficulty",
    #     "Effort",
    #     "Time",
    #     "Estimated Bugs",
    # )
    # SECTIONS: Tuple[Tuple[str, Tuple[str]]] = (
    #     ("Core", CORE_KEYS),
    #     ("Extended1", EXTENDED1_KEYS),
    #     ("Extended2", EXTENDED2_KEYS),
    # )

    def __post_init__(self):
        # # Compute the metrics for each contract and for all contracts.
        # for contract in self.contracts:
        #     self.contract_metrics[contract.name] = HalsteadContractMetrics(contract=contract)

        # # If there are more than 1 contract, compute the metrics for all contracts.
        # if len(self.contracts) > 1:
        #     all_operators = [
        #         operator
        #         for contract in self.contracts
        #         for operator in self.contract_metrics[contract.name].all_operators
        #     ]
        #     all_operands = [
        #         operand
        #         for contract in self.contracts
        #         for operand in self.contract_metrics[contract.name].all_operands
        #     ]
        #     self.contract_metrics["ALL CONTRACTS"] = HalsteadContractMetrics(
        #         None, all_operators=all_operators, all_operands=all_operands
        #     )
        pass

        # Create the table and text for each section.
        data = {
            contract.name: self.contract_metrics[contract.name].to_dict()
            for contract in self.contracts
        }
        for (title, keys) in self.SECTIONS:
            pretty_table = make_pretty_table(["Contract", *keys], data, False)
            section_title = f"{self.title} ({title})"
            txt = f"\n\n{section_title}:\n{pretty_table}\n"
            self.full_txt += txt
            setattr(
                self,
                title.lower(),
                SectionInfo(title=section_title, pretty_table=pretty_table, txt=txt),
            )
