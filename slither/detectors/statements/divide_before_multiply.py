"""
Module detecting possible loss of precision due to divide before multiple
"""
from collections import defaultdict
from typing import DefaultDict, List, Tuple

from slither.core.cfg.node import Node
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import Binary, Assignment, BinaryType, LibraryCall, Operation
from slither.slithir.utils.utils import LVALUE
from slither.slithir.variables import Constant
from slither.utils.output import Output


def is_division(ir: Operation) -> bool:
    if isinstance(ir, Binary):
        if ir.type == BinaryType.DIVISION:
            return True

    if isinstance(ir, LibraryCall):
        if ir.function.name and ir.function.name.lower() in [
            "div",
            "safediv",
        ]:
            if len(ir.arguments) == 2:
                if ir.lvalue:
                    return True
    return False


def is_multiplication(ir: Operation) -> bool:
    if isinstance(ir, Binary):
        if ir.type == BinaryType.MULTIPLICATION:
            return True

    if isinstance(ir, LibraryCall):
        if ir.function.name and ir.function.name.lower() in [
            "mul",
            "safemul",
        ]:
            if len(ir.arguments) == 2:
                if ir.lvalue:
                    return True
    return False


def is_assert(node: Node) -> bool:
    if node.contains_require_or_assert():
        return True
    # Old Solidity code where using an internal 'assert(bool)' function
    # While we dont check that this function is correct, we assume it is
    # To avoid too many FP
    if "assert(bool)" in [c.full_name for c in node.internal_calls]:
        return True
    return False


# pylint: disable=too-many-branches
def _explore(
    to_explore: List[Node], f_results: List[List[Node]], divisions: DefaultDict[LVALUE, List[Node]]
) -> None:
    explored = set()
    while to_explore:  # pylint: disable=too-many-nested-blocks
        node = to_explore.pop()

        if node in explored:
            continue
        explored.add(node)

        equality_found = False
        # List of nodes related to one bug instance
        node_results: List[Node] = []

        for ir in node.irs:
            if isinstance(ir, Assignment):
                if ir.rvalue in divisions:
                    # Avoid dupplicate. We dont use set so we keep the order of the nodes
                    if node not in divisions[ir.rvalue]:  # type: ignore
                        divisions[ir.lvalue] = divisions[ir.rvalue] + [node]  # type: ignore
                    else:
                        divisions[ir.lvalue] = divisions[ir.rvalue]  # type: ignore

            if is_division(ir):
                divisions[ir.lvalue] = [node]  # type: ignore

            if is_multiplication(ir):
                mul_arguments = ir.read if isinstance(ir, Binary) else ir.arguments  # type: ignore
                nodes = []
                for r in mul_arguments:
                    if not isinstance(r, Constant) and (r in divisions):
                        # Dont add node already present to avoid dupplicate
                        # We dont use set to keep the order of the nodes
                        if node in divisions[r]:
                            nodes += [n for n in divisions[r] if n not in nodes]
                        else:
                            nodes += [n for n in divisions[r] + [node] if n not in nodes]
                if nodes:
                    node_results = nodes

            if isinstance(ir, Binary) and ir.type == BinaryType.EQUAL:
                equality_found = True

        if node_results:
            # We do not track the case where the multiplication is done in a require() or assert()
            # Which also contains a ==, to prevent FP due to the form
            # assert(a == b * c + a % b)
            if not (is_assert(node) and equality_found):
                f_results.append(node_results)

        for son in node.sons:
            to_explore.append(son)


def detect_divide_before_multiply(
    contract: Contract,
) -> List[Tuple[FunctionContract, List[Node]]]:
    """
    Detects and returns all nodes with multiplications of division results.
    :param contract: Contract to detect assignment within.
    :return: A list of nodes with multiplications of divisions.
    """

    # Create our result set.
    # List of tuple (function -> list(list(nodes)))
    # Each list(nodes) of the list is one bug instances
    # Each node in the list(nodes) is involved in the bug
    results: List[Tuple[FunctionContract, List[Node]]] = []

    # Loop for each function and modifier.
    for function in contract.functions_declared:
        if not function.entry_point:
            continue

        # List of list(nodes)
        # Each list(nodes) is one bug instances
        f_results: List[List[Node]] = []

        # lvalue -> node
        # track all the division results (and the assignment of the division results)
        divisions: DefaultDict[LVALUE, List[Node]] = defaultdict(list)

        _explore([function.entry_point], f_results, divisions)

        for f_result in f_results:
            results.append((function, f_result))

    # Return the resulting set of nodes with divisions before multiplications
    return results


class DivideBeforeMultiply(AbstractDetector):
    """
    Divide before multiply
    """

    ARGUMENT = "divide-before-multiply"
    HELP = "Imprecise arithmetic operations order"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#divide-before-multiply"

    WIKI_TITLE = "Divide before multiply"
    WIKI_DESCRIPTION = """Solidity's integer division truncates. Thus, performing division before multiplication can lead to precision loss."""

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract A {
	function f(uint n) public {
        coins = (oldSupply / n) * interest;
    }
}
```
If `n` is greater than `oldSupply`, `coins` will be zero. For example, with `oldSupply = 5; n = 10, interest = 2`, coins will be zero.  
If `(oldSupply * interest / n)` was used, `coins` would have been `1`.   
In general, it's usually a good idea to re-arrange arithmetic to perform multiplication before division, unless the limit of a smaller type makes this dangerous."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """Consider ordering multiplication before division."""

    def _detect(self) -> List[Output]:
        """
        Detect divisions before multiplications
        """
        results = []
        for contract in self.contracts:
            divisions_before_multiplications = detect_divide_before_multiply(contract)
            if divisions_before_multiplications:
                for (func, nodes) in divisions_before_multiplications:

                    info: DETECTOR_INFO = [
                        func,
                        " performs a multiplication on the result of a division:\n",
                    ]

                    # sort the nodes to get deterministic results
                    nodes.sort(key=lambda x: x.node_id)

                    for node in nodes:
                        info += ["\t- ", node, "\n"]

                    res = self.generate_result(info)
                    results.append(res)

        return results
