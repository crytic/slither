"""
    Halstead complexity metrics
    https://en.wikipedia.org/wiki/Halstead_complexity_measures

    12 metrics based on the number of unique operators and operands:

    Core metrics:
    n1 = the number of distinct operators
    n2 = the number of distinct operands
    N1 = the total number of operators
    N2 = the total number of operands

    Extended metrics1:
    n = n1 + n2  # Program vocabulary
    N = N1 + N2  # Program length
    S = n1 * log2(n1) + n2 * log2(n2) # Estimated program length
    V = N * log2(n) # Volume

    Extended metrics2:
    D = (n1 / 2) * (N2 / n2) # Difficulty
    E = D * V # Effort
    T = E / 18 seconds # Time required to program
    B = (E^(2/3)) / 3000 # Number of delivered bugs


"""
import math
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Tuple, List, Dict

from slither.core.declarations import Contract
from slither.slithir.variables.temporary import TemporaryVariable
from slither.utils.encoding import encode_ir_for_halstead
from slither.utils.myprettytable import make_pretty_table, MyPrettyTable


# pylint: disable=too-many-branches


@dataclass
# pylint: disable=too-many-instance-attributes
class HalsteadContractMetrics:
    """Class to hold the Halstead metrics for a single contract."""

    contract: Contract
    all_operators: List[str] = field(default_factory=list)
    all_operands: List[str] = field(default_factory=list)
    n1: int = 0
    n2: int = 0
    N1: int = 0
    N2: int = 0
    n: int = 0
    N: int = 0
    S: float = 0
    V: float = 0
    D: float = 0
    E: float = 0
    T: float = 0
    B: float = 0

    def __post_init__(self) -> None:
        """Operators and operands can be passed in as constructor args to avoid computing
        them based on the contract. Useful for computing metrics for ALL_CONTRACTS"""

        if len(self.all_operators) == 0:
            if not hasattr(self.contract, "functions"):
                return
            self.populate_operators_and_operands()
        if len(self.all_operators) > 0:
            self.compute_metrics()

    def to_dict(self) -> Dict[str, float]:
        """Return the metrics as a dictionary."""
        return OrderedDict(
            {
                "Total Operators": self.N1,
                "Unique Operators": self.n1,
                "Total Operands": self.N2,
                "Unique Operands": self.n2,
                "Vocabulary": str(self.n1 + self.n2),
                "Program Length": str(self.N1 + self.N2),
                "Estimated Length": f"{self.S:.0f}",
                "Volume": f"{self.V:.0f}",
                "Difficulty": f"{self.D:.0f}",
                "Effort": f"{self.E:.0f}",
                "Time": f"{self.T:.0f}",
                "Estimated Bugs": f"{self.B:.3f}",
            }
        )

    def populate_operators_and_operands(self) -> None:
        """Populate the operators and operands lists."""
        operators = []
        operands = []

        for func in self.contract.functions:
            for node in func.nodes:
                for operation in node.irs:
                    # use operation.expression.type to get the unique operator type
                    encoded_operator = encode_ir_for_halstead(operation)
                    operators.append(encoded_operator)

                    # use operation.used to get the operands of the operation ignoring the temporary variables
                    operands.extend(
                        [op for op in operation.used if not isinstance(op, TemporaryVariable)]
                    )
        self.all_operators.extend(operators)
        self.all_operands.extend(operands)

    def compute_metrics(self, all_operators=None, all_operands=None) -> None:
        """Compute the Halstead metrics."""
        if all_operators is None:
            all_operators = self.all_operators
            all_operands = self.all_operands

        # core metrics
        self.n1 = len(set(all_operators))
        self.n2 = len(set(all_operands))
        self.N1 = len(all_operators)
        self.N2 = len(all_operands)
        if any(number <= 0 for number in [self.n1, self.n2, self.N1, self.N2]):
            raise ValueError("n1 and n2 must be greater than 0")

        # extended metrics 1
        self.n = self.n1 + self.n2
        self.N = self.N1 + self.N2
        self.S = self.n1 * math.log2(self.n1) + self.n2 * math.log2(self.n2)
        self.V = self.N * math.log2(self.n)

        # extended metrics 2
        self.D = (self.n1 / 2) * (self.N2 / self.n2)
        self.E = self.D * self.V
        self.T = self.E / 18
        self.B = (self.E ** (2 / 3)) / 3000


@dataclass
class SectionInfo:
    """Class to hold the information for a section of the report."""

    title: str
    pretty_table: MyPrettyTable
    txt: str


@dataclass
# pylint: disable=too-many-instance-attributes
class HalsteadMetrics:
    """Class to hold the Halstead metrics for all contracts. Contains methods useful for reporting.

    There are 3 sections in the report:
    1. Core metrics (n1, n2, N1, N2)
    2. Extended metrics 1 (n, N, S, V)
    3. Extended metrics 2 (D, E, T, B)

    """

    contracts: List[Contract] = field(default_factory=list)
    contract_metrics: OrderedDict = field(default_factory=OrderedDict)
    title: str = "Halstead complexity metrics"
    full_text: str = ""
    core: SectionInfo = field(default=SectionInfo)
    extended1: SectionInfo = field(default=SectionInfo)
    extended2: SectionInfo = field(default=SectionInfo)
    CORE_KEYS = (
        "Total Operators",
        "Unique Operators",
        "Total Operands",
        "Unique Operands",
    )
    EXTENDED1_KEYS = (
        "Vocabulary",
        "Program Length",
        "Estimated Length",
        "Volume",
    )
    EXTENDED2_KEYS = (
        "Difficulty",
        "Effort",
        "Time",
        "Estimated Bugs",
    )
    SECTIONS: Tuple[Tuple[str, str, Tuple[str]]] = (
        ("Core", "core", CORE_KEYS),
        ("Extended 1/2", "extended1", EXTENDED1_KEYS),
        ("Extended 2/2", "extended2", EXTENDED2_KEYS),
    )

    def __post_init__(self) -> None:
        # Compute the metrics for each contract and for all contracts.
        self.update_contract_metrics()
        self.add_all_contracts_metrics()
        self.update_reporting_sections()

    def update_contract_metrics(self) -> None:
        for contract in self.contracts:
            self.contract_metrics[contract.name] = HalsteadContractMetrics(contract=contract)

    def add_all_contracts_metrics(self) -> None:
        # If there are more than 1 contract, compute the metrics for all contracts.
        if len(self.contracts) <= 1:
            return
        all_operators = [
            operator
            for contract in self.contracts
            for operator in self.contract_metrics[contract.name].all_operators
        ]
        all_operands = [
            operand
            for contract in self.contracts
            for operand in self.contract_metrics[contract.name].all_operands
        ]
        self.contract_metrics["ALL CONTRACTS"] = HalsteadContractMetrics(
            None, all_operators=all_operators, all_operands=all_operands
        )

    def update_reporting_sections(self) -> None:
        # Create the table and text for each section.
        data = {
            contract.name: self.contract_metrics[contract.name].to_dict()
            for contract in self.contracts
        }
        for (title, attr, keys) in self.SECTIONS:
            pretty_table = make_pretty_table(["Contract", *keys], data, False)
            section_title = f"{self.title} ({title})"
            txt = f"\n\n{section_title}:\n{pretty_table}\n"
            self.full_text += txt
            setattr(
                self,
                attr,
                SectionInfo(title=section_title, pretty_table=pretty_table, txt=txt),
            )
