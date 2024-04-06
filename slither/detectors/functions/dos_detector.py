from typing import List, Optional
from enum import Enum
from slither.core.cfg.node import NodeType, Node
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.core.solidity_types import ElementaryType
from slither.slithir.variables import Constant
from slither.core.declarations import Contract
from slither.utils.output import Output
from slither.slithir.operations import Condition


def detect_infinite_loop_calls(contract: Contract) -> List[Node]:
    ret: List[Node] = []
    for f in contract.functions_entry_points:
        if f.is_implemented:
            detect_infinite_calls(f.entry_point, [], ret)

    return ret


def detect_infinite_calls(node: Optional[Node], visited: List[Node], ret: List[Node]) -> None:
    if node is None:
        return
    if node in visited:
        return
    # Add node to visited list
    visited.append(node)

    # Check if node represents a loop
    if node.type == NodeType.STARTLOOP:
        # Check if the loop has a proper exit condition
        if not has_exit_condition(node):
            ret.append(node)
    elif node.type == NodeType.ENDLOOP:
        pass

    # Recursively traverse the graph
    for son in node.sons:
        detect_infinite_calls(son, visited, ret)


def has_exit_condition(node: Node) -> bool:
    if node.type == NodeType.STARTLOOP:
        for son in node.sons:
            # Check if the son node represents a condition
            if son.type in [NodeType.WHILELOOP, NodeType.IFLOOP]:
                # if son.type == NodeType.WHILELOOP:
                return True  # Exit condition found
        return False  # No condition found within the loop
    else:
        return False  # The given node is not a loop

    # Example usage:
    # Assuming 'node' is a Node object representing a loop
    if has_exit_condition(node):
        print("The loop has an exit condition.")
    else:
        print("The loop does not have an exit condition.")


class DOSDetector(AbstractDetector):
    ARGUMENT = "dosdetector"
    HELP = "Detects potential Denial of Service (DoS) vulnerabilities"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#dos-vulnerabilities"

    WIKI_TITLE = "DoS Vulnerabilities"
    WIKI_DESCRIPTION = "Detects functions that may lead to Denial of Service (DoS) attacks"
    WIKI_EXPLOIT_SCENARIO = "An attacker may exploit this vulnerability by repeatedly calling the vulnerable function with large input arrays, causing the contract to consume excessive gas and potentially leading to a DoS attack."

    WIKI_RECOMMENDATION = "To mitigate DOS vulnerabilities, developers should carefully analyze their contract's public functions and ensure that they are optimized to handle potential attacks. Functions that are not intended to be called externally should be declared as `internal` or `private`, and critical functions should implement gas limits or use mechanisms such as rate limiting to prevent abuse."

    def _detect(self) -> List[Output]:
        results: List[Output] = []
        for c in self.compilation_unit.contracts_derived:
            values = detect_infinite_loop_calls(c)
            for node in values:
                func = node.function

                info: DETECTOR_INFO = [
                    func,
                    " contains a loop without proper exit condition: ",
                    node,
                    "\n",
                ]
                res = self.generate_result(info)
                results.append(res)

        return results
