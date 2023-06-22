"""
    Module detecting dangerous use of block.timestamp

"""
from typing import List, Tuple

from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.cfg.node import Node
from slither.core.declarations import Function, Contract, FunctionContract
from slither.core.declarations.solidity_variables import (
    SolidityVariableComposed,
    SolidityVariable,
)
from slither.core.variables import Variable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import Binary, BinaryType
from slither.utils.output import Output


def _timestamp(func: Function) -> List[Node]:
    ret = set()
    for node in func.nodes:
        if node.contains_require_or_assert():
            for var in node.variables_read:
                if is_dependent(var, SolidityVariableComposed("block.timestamp"), node):
                    ret.add(node)
                if is_dependent(var, SolidityVariable("now"), node):
                    ret.add(node)
        for ir in node.irs:
            if isinstance(ir, Binary) and BinaryType.return_bool(ir.type):
                for var_read in ir.read:
                    if not isinstance(var_read, (Variable, SolidityVariable)):
                        continue
                    if is_dependent(var_read, SolidityVariableComposed("block.timestamp"), node):
                        ret.add(node)
                    if is_dependent(var_read, SolidityVariable("now"), node):
                        ret.add(node)
    return sorted(list(ret), key=lambda x: x.node_id)


def _detect_dangerous_timestamp(
    contract: Contract,
) -> List[Tuple[FunctionContract, List[Node]]]:
    """
    Args:
        contract (Contract)
    Returns:
        list((Function), (list (Node)))
    """
    ret = []
    for f in [f for f in contract.functions if f.contract_declarer == contract]:
        nodes: List[Node] = _timestamp(f)
        if nodes:
            ret.append((f, nodes))
    return ret


class Timestamp(AbstractDetector):

    ARGUMENT = "timestamp"
    HELP = "Dangerous usage of `block.timestamp`"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#block-timestamp"

    WIKI_TITLE = "Block timestamp"
    WIKI_DESCRIPTION = (
        "Dangerous usage of `block.timestamp`. `block.timestamp` can be manipulated by miners."
    )
    WIKI_EXPLOIT_SCENARIO = """"Bob's contract relies on `block.timestamp` for its randomness. Eve is a miner and manipulates `block.timestamp` to exploit Bob's contract."""
    WIKI_RECOMMENDATION = "Avoid relying on `block.timestamp`."

    def _detect(self) -> List[Output]:
        """"""
        results = []

        for c in self.contracts:
            dangerous_timestamp = _detect_dangerous_timestamp(c)
            for (func, nodes) in dangerous_timestamp:

                info: DETECTOR_INFO = [func, " uses timestamp for comparisons\n"]

                info += ["\tDangerous comparisons:\n"]

                # sort the nodes to get deterministic results
                nodes.sort(key=lambda x: x.node_id)

                for node in nodes:
                    info += ["\t- ", node, "\n"]

                res = self.generate_result(info)

                results.append(res)

        return results
