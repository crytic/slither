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
from dataclasses import dataclass, field
from typing import Tuple, List, Dict
from collections import OrderedDict
from slither.core.declarations import (
    Contract,
    Pragma,
    Import,
    Function,
    Modifier,
)
from slither.printers.abstract_printer import AbstractPrinter
from slither.slithir.variables.temporary import TemporaryVariable
from slither.utils.myprettytable import make_pretty_table, MyPrettyTable
from slither.utils.upgradeability import encode_ir_for_halstead # TODO: Add to slither/utils/halstead


@dataclass
class HalsteadContractMetrics:
    """Class to hold the Halstead metrics for a single contract."""
    # TODO: Add to slither/utils/halstead
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

    def __post_init__(self):
        if (len(self.all_operators) == 0):
            self.populate_operators_and_operands()
        self.compute_metrics()

    def to_dict(self) -> Dict[str, float]:
        """Return the metrics as a dictionary."""
        return OrderedDict({
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
        })

    def populate_operators_and_operands(self):
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
                    operands.extend([
                        op for op in operation.used if not isinstance(op, TemporaryVariable)
                    ])
        # import pdb; pdb.set_trace()
        self.all_operators.extend(operators)
        self.all_operands.extend(operands)

    def compute_metrics(self, all_operators=[], all_operands=[]):
        """Compute the Halstead metrics."""
        if len(all_operators) == 0:
            all_operators = self.all_operators
            all_operands = self.all_operands

        self.n1 = len(set(all_operators))
        self.n2 = len(set(all_operands))
        self.N1 = len(all_operators)
        self.N2 = len(all_operands)
        if any(number <= 0 for number in [self.n1, self.n2, self.N1, self.N2]):
            raise ValueError("n1 and n2 must be greater than 0")

        self.n = self.n1 + self.n2
        self.N = self.N1 + self.N2
        self.S = self.n1 * math.log2(self.n1) + self.n2 * math.log2(self.n2)
        self.V = self.N * math.log2(self.n)
        self.D = (self.n1 / 2) * (self.N2 / self.n2)
        self.E = self.D * self.V
        self.T = self.E / 18
        self.B = (self.E ** (2 / 3)) / 3000


@dataclass
class SectionInfo:
    title: str
    pretty_table: MyPrettyTable
    txt: str


@dataclass
class HalsteadMetrics:
    """Class to hold the Halstead metrics for all contracts and methods for reporting."""
    contracts: List[Contract] = field(default_factory=list)
    contract_metrics: OrderedDict[Contract, HalsteadContractMetrics] = field(default_factory=OrderedDict)
    title: str = "Halstead complexity metrics"
    full_txt: str = ""
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
    SECTIONS: Tuple[Tuple[str, Tuple[str]]] = (
        ("Core", CORE_KEYS),
        ("Extended1", EXTENDED1_KEYS),
        ("Extended2", EXTENDED2_KEYS),
    )


    def __post_init__(self):
        for contract in self.contracts:
            self.contract_metrics[contract.name] = HalsteadContractMetrics(contract=contract)

        if len(self.contracts) > 1:
            all_operators = [
                operator for contract in self.contracts
                for operator in self.contract_metrics[contract.name].all_operators
            ]

            all_operands = [
                operand for contract in self.contracts
                for operand in self.contract_metrics[contract.name].all_operands
            ]

            self.contract_metrics["ALL CONTRACTS"] = HalsteadContractMetrics(all_operators=all_operators, all_operands=all_operands)

        data = {
            contract.name: self.contract_metrics[contract.name].to_dict()
            for contract in self.contracts
        }
        for (title, keys) in self.SECTIONS:
            pretty_table = make_pretty_table(["Contract", *keys], data, False)
            section_title = f"{self.title} - {title}"
            txt = f"\n\n{section_title}:\n{pretty_table}\n"
            self.full_txt += txt
            setattr(self, title.lower(), SectionInfo(title=section_title, pretty_table=pretty_table, txt=txt))

def compute_halstead(contracts: list) -> Tuple[Dict, Dict, Dict]:
    """Used to compute the Halstead complexity metrics for a list of contracts.
    Args:
        contracts: list of contracts.
    Returns:
        Halstead metrics as a tuple of three OrderedDicts (core_metrics, extended_metrics1, extended_metrics2)
        which each contain one key per contract. The value of each key is a dict of metrics.

        In addition to one key per contract, there is a key for "ALL CONTRACTS" that contains
        the metrics for ALL CONTRACTS combined. (Not the sums of the individual contracts!)

        core_metrics:
        {"contract1 name": {
            "N1_total_operators": N1,
            "n1_unique_operators": n1,
            "N2_total_operands": N2,
            "n2_unique_operands": n1,
        }}

        extended_metrics1:
        {"contract1 name": {
            "n_vocabulary": n1 + n2,
            "N_prog_length": N1 + N2,
            "S_est_length": S,
            "V_volume": V,
        }}
        extended_metrics2:
        {"contract1 name": {
            "D_difficulty": D,
            "E_effort": E,
            "T_time": T,
            "B_bugs": B,
        }}

    """
    core = OrderedDict()
    extended1 = OrderedDict()
    extended2 = OrderedDict()
    all_operators = []
    all_operands = []
    for contract in contracts:
        operators = []
        operands = []
        for func in contract.functions:
            for node in func.nodes:
                for operation in node.irs:
                    # use operation.expression.type to get the unique operator type
                    encoded_operator = encode_ir_for_halstead(operation)
                    operators.append(encoded_operator)
                    all_operators.append(encoded_operator)

                    # use operation.used to get the operands of the operation ignoring the temporary variables
                    new_operands = [
                        op for op in operation.used if not isinstance(op, TemporaryVariable)
                    ]
                    operands.extend(new_operands)
                    all_operands.extend(new_operands)
        (
            core[contract.name],
            extended1[contract.name],
            extended2[contract.name],
        ) = _calculate_metrics(operators, operands)
    if len(contracts) > 1:
        core["ALL CONTRACTS"] = OrderedDict()
        extended1["ALL CONTRACTS"] = OrderedDict()
        extended2["ALL CONTRACTS"] = OrderedDict()
        (
            core["ALL CONTRACTS"],
            extended1["ALL CONTRACTS"],
            extended2["ALL CONTRACTS"],
        ) = _calculate_metrics(all_operators, all_operands)
    return (core, extended1, extended2)


# pylint: disable=too-many-locals
def _calculate_metrics(operators, operands):
    """Used to compute the Halstead complexity metrics for a list of operators and operands.
    Args:
        operators: list of operators.
        operands: list of operands.
    Returns:
        Halstead metrics as a tuple of two OrderedDicts (core_metrics, extended_metrics)
        which each contain one key per contract. The value of each key is a dict of metrics.
        NOTE: The metric values are ints and floats that have been converted to formatted strings
    """
    n1 = len(set(operators))
    n2 = len(set(operands))
    N1 = len(operators)
    N2 = len(operands)
    n = n1 + n2
    N = N1 + N2
    S = 0 if (n1 == 0 or n2 == 0) else n1 * math.log2(n1) + n2 * math.log2(n2)
    V = N * math.log2(n) if n > 0 else 0
    D = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
    E = D * V
    T = E / 18
    B = (E ** (2 / 3)) / 3000
    core_metrics = {
        "Total Operators": N1,
        "Unique Operators": n1,
        "Total Operands": N2,
        "Unique Operands": n2,
    }
    extended_metrics1 = {
        "Vocabulary": str(n1 + n2),
        "Program Length": str(N1 + N2),
        "Estimated Length": f"{S:.0f}",
        "Volume": f"{V:.0f}",
    }
    extended_metrics2 = {
        "Difficulty": f"{D:.0f}",
        "Effort": f"{E:.0f}",
        "Time": f"{T:.0f}",
        "Estimated Bugs": f"{B:.3f}",
    }
    return (core_metrics, extended_metrics1, extended_metrics2)


class Halstead(AbstractPrinter):
    ARGUMENT = "halstead"
    HELP = "Computes the Halstead complexity metrics for each contract"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#halstead"

    def output(self, _filename):
        if len(self.contracts) == 0:
            return self.generate_output("No contract found")

        core, extended1, extended2 = compute_halstead(self.contracts)

        halstead = HalsteadMetrics(self.contracts)

        # Core metrics: operations and operands
        txt = "\n\nHalstead complexity core metrics:\n"
        keys = list(core[self.contracts[0].name].keys())
        table_core = make_pretty_table(["Contract", *keys], core, False)
        txt += str(table_core) + "\n"

        # Extended metrics1: vocabulary, program length, estimated length, volume
        txt += "\nHalstead complexity extended metrics1:\n"
        keys = list(extended1[self.contracts[0].name].keys())
        table_extended1 = make_pretty_table(["Contract", *keys], extended1, False)
        txt += str(table_extended1) + "\n"

        # Extended metrics2: difficulty, effort, time, bugs
        txt += "\nHalstead complexity extended metrics2:\n"
        keys = list(extended2[self.contracts[0].name].keys())
        table_extended2 = make_pretty_table(["Contract", *keys], extended2, False)
        txt += str(table_extended2) + "\n"

        res = self.generate_output(txt)
        res.add_pretty_table(table_core, "Halstead core metrics")
        res.add_pretty_table(table_extended1, "Halstead extended metrics1")
        res.add_pretty_table(table_extended2, "Halstead extended metrics2")
        self.info(txt)
        self.info("*****************************************************************")
        self.info("new one")
        self.info("*****************************************************************")
        self.info(halstead.full_txt)

        return res
