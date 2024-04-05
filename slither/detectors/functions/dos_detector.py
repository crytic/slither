from typing import List, Optional
from slither.core.cfg.node import NodeType, Node
from enum import Enum
from typing import List, Set, Tuple
from slither.core.declarations import Function
from slither.core.solidity_types import ElementaryType
from slither.slithir.variables import Constant
from slither.core.declarations import Contract
from slither.utils.output import Output
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import (
    HighLevelCall,
    LibraryCall,
    LowLevelCall,
    Send,
    Transfer,
    InternalCall,
    Assignment,
    Call,
    Return,
    InitArray,
    Binary,
    BinaryType,
    Condition,
)


def detect_infinite_loop_calls(contract: Contract) -> List[Node]:
    ret: List[Node] = []
    for f in contract.functions_entry_points:
        if f.is_implemented:
            detect_infinite_calls(f.entry_point, [], ret)

    return ret


def detect_infinite_calls(
    node: Optional[Node], visited: List[Node], ret: List[Node]
) -> None:
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
    """
    Check if the loop represented by the given node has a proper exit condition.

    Args:
    - node: The node representing the loop in the control flow graph.

    Returns:
    - True if the loop has a proper exit condition, False otherwise.
    """
    # We assume the loop has an exit condition by default
    exit_condition_found = True

    # Check for special case: "while(true)"
    if node.type == NodeType.IFLOOP and node.irs and len(node.irs) == 1:
        ir = node.irs[0]
        if isinstance(ir, Condition) and ir.value == Constant(
            "True", ElementaryType("bool")
        ):
            exit_condition_found = False
            return exit_condition_found  # Return immediately if it's a while(true) loop 

    # Traverse through the sons of the loop node to find the exit condition
    for son in node.sons:
        # Check if the son node is a condition node
        if son.type == NodeType.CONDITION:
            # If the condition node has an exit edge, it indicates a proper exit condition
            if son.sons:
                exit_condition_found = True
            # If the condition node doesn't have an exit edge, it may indicate an infinite loop
            else:
                exit_condition_found = False
            break  # Exit the loop after finding a condition node

    return exit_condition_found

class DOSDetector(AbstractDetector):
    ARGUMENT = 'dosdetector'
    HELP = "Detects potential Denial of Service (DoS) vulnerabilities"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://example.com/wiki/dos-vulnerabilities"

    WIKI_TITLE = "DoS Vulnerabilities"
    WIKI_DESCRIPTION = "Detects functions that may lead to Denial of Service (DoS) attacks"
    WIKI_EXPLOIT_SCENARIO = "An attacker may exploit this vulnerability by repeatedly calling the vulnerable function with large input arrays, causing the contract to consume excessive gas and potentially leading to a DoS attack."

    WIKI_RECOMMENDATION = "To mitigate DOS vulnerabilities, developers should carefully analyze their contract's public functions and ensure that they are optimized to handle potential attacks. Functions that are not intended to be called externally should be declared as `internal` or `private`, and critical functions should implement gas limits or use mechanisms such as rate limiting to prevent abuse."
    
    def _detect(self) -> List[Output]:
        """"""
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
