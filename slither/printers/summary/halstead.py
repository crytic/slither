"""
    Halstead complexity metrics
    https://en.wikipedia.org/wiki/Halstead_complexity_measures

    12 metrics based on the number of unique operators and operands:

    Core metrics:
    n1 = the number of distinct operators
    n2 = the number of distinct operands
    N1 = the total number of operators
    N2 = the total number of operands

    Extended metrics:
    n = n1 + n2  # Program vocabulary
    N = N1 + N2  # Program length
    S = n1 * log2(n1) + n2 * log2(n2) # Estimated program length
    V = N * log2(n) # Volume
    D = (n1 / 2) * (N2 / n2) # Difficulty
    E = D * V # Effort
    T = E / 18 seconds # Time required to program
    B = (E^(2/3)) / 3000 # Number of delivered bugs


"""
import math
from collections import OrderedDict
from slither.printers.abstract_printer import AbstractPrinter
from slither.slithir.variables.temporary import TemporaryVariable
from slither.utils.myprettytable import make_pretty_table


def compute_halstead(contracts: list) -> tuple:
    """Used to compute the Halstead complexity metrics for a list of contracts.
    Args:
        contracts: list of contracts.
    Returns:
        Halstead metrics as a tuple of two OrderedDicts (core_metrics, extended_metrics)
        which each contain one key per contract. The value of each key is a dict of metrics.

        In addition to one key per contract, there is a key for "ALL CONTRACTS" that contains
        the metrics for ALL CONTRACTS combined. (Not the sums of the individual contracts!)

        core_metrics:
        {"contract1 name": {
            "n1_unique_operators": n1,
            "n2_unique_operands": n1,
            "N1_total_operators": N1,
            "N2_total_operands": N2,
        }}

        extended_metrics:
        {"contract1 name": {
            "n_vocabulary": n1 + n2,
            "N_prog_length": N1 + N2,
            "S_est_length": S,
            "V_volume": V,
            "D_difficulty": D,
            "E_effort": E,
            "T_time": T,
            "B_bugs": B,
        }}

    """
    core = OrderedDict()
    extended = OrderedDict()
    all_operators = []
    all_operands = []
    for contract in contracts:
        operators = []
        operands = []
        for func in contract.functions:
            for node in func.nodes:
                for operation in node.irs:
                    # use operation.expression.type to get the unique operator type
                    # TODO: This is broken. It considers every operation as a unique operator.
                    operators.append(operation)
                    all_operators.append(operation)

                    # use operation.used to get the operands of the operation ignoring the temporary variables
                    new_operands = [
                        op for op in operation.used if not isinstance(op, TemporaryVariable)
                    ]
                    operands.extend(new_operands)
                    all_operands.extend(new_operands)
        (core[contract.name], extended[contract.name]) = _calculate_metrics(operators, operands)
    core["ALL CONTRACTS"] = OrderedDict()
    extended["ALL CONTRACTS"] = OrderedDict()
    (core["ALL CONTRACTS"], extended["ALL CONTRACTS"]) = _calculate_metrics(
        all_operators, all_operands
    )
    return (core, extended)


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
        "n1_unique_operators": n1,
        "n2_unique_operands": n2,
        "N1_total_operators": N1,
        "N2_total_operands": N2,
    }
    extended_metrics = {
        "n_vocabulary": str(n1 + n2),
        "N_prog_length": str(N1 + N2),
        "S_est_length": f"{S:.0f}",
        "V_volume": f"{V:.0f}",
        "D_difficulty": f"{D:.0f}",
        "E_effort": f"{E:.0f}",
        "T_time": f"{T:.0f}",
        "B_bugs": f"{B:.3f}",
    }
    return (core_metrics, extended_metrics)


class Halstead(AbstractPrinter):
    ARGUMENT = "halstead"
    HELP = "Computes the Halstead complexity metrics for each contract"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#halstead"

    def output(self, _filename):
        if len(self.contracts) == 0:
            return self.generate_output("No contract found")

        core, extended = compute_halstead(self.contracts)

        # Core metrics: operations and operands
        txt = "\n\nHalstead complexity core metrics:\n"
        keys = list(core[self.contracts[0].name].keys())
        table1 = make_pretty_table(["Contract", *keys], core, False)
        txt += str(table1) + "\n"

        # Extended metrics: volume, difficulty, effort, time, bugs
        # TODO: should we break this into 2 tables? currently 119 chars wide
        txt += "\nHalstead complexity extended metrics:\n"
        keys = list(extended[self.contracts[0].name].keys())
        table2 = make_pretty_table(["Contract", *keys], extended, False)
        txt += str(table2) + "\n"

        res = self.generate_output(txt)
        res.add_pretty_table(table1, "Halstead core metrics")
        res.add_pretty_table(table2, "Halstead extended metrics")
        self.info(txt)

        return res
