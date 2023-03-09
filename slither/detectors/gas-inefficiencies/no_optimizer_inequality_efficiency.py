"""
Gas: If the optimizer is disabled, using ! = 0 outside of a require statement is slightly more gas efficient than using > 0. Same costs for a require.

"""   

from slither.detectors.abstract_detector import DetectorClassification, AbstractDetector
from slither.core.cfg.node import NodeType
from slither.core.solidity_types.type import Type

ARGUMENT = "no-optimizer-inequality-efficiency"
HELP = "Consider using ! = 0 outside of any require statements rather than > = 0 to save gas."
IMPACT = DetectorClassification.OPTIMIZATION
CONFIDENCE = DetectorClassification.MEDIUM

WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#-0-is-cheaper-than--0-sometimes"
WIKI_TITLE = "> 0 is cheaper than ! = 0 sometimes."
WIKI_DESCRIPTION = "With optimizer disabled, using the ! = 0 inequality outside of any require statements is slightly more gas efficient than using > 0." 

def _detect(contract, _):
    issues = []
    for function in contract.functions:
        cfg = function.cfg
        for node in cfg.nodes:
            if node.type == NodeType.ASSIGNMENT:
                if isinstance(node.variable.type, Type) and node.expression:
                    expression = node.expression
                    if expression.operator == ">=" and isinstance(expression.left.type, Type) and isinstance(expression.right.type, Type):
                        if expression.left.type.name in ["int256", "uint256"] and expression.right.type.name in ["int256", "uint256"]:
                            if not any([parent for parent in expression.parents if parent.type == NodeType.EXPRESSION and parent.expression.operator == "!="]):
                                issues.append(f"Use of >= 0 outside of require statement in function {function.name}")
    return issues
