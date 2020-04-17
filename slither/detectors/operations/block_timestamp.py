"""
    Module detecting dangerous use of block.timestamp

"""
from typing import List, Tuple

from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.cfg.node import Node
from slither.core.declarations import Function, Contract
from slither.core.declarations.solidity_variables import (SolidityVariableComposed, SolidityVariable)
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import Binary, BinaryType


def _timestamp(func: Function) -> List[Node]:
    ret = set()
    for node in func.nodes:
        if node.contains_require_or_assert():
            for var in node.variables_read:
                if is_dependent(var, SolidityVariableComposed('block.timestamp'), func.contract):
                    ret.add(node)
                if is_dependent(var, SolidityVariable('now'), func.contract):
                    ret.add(node)
        for ir in node.irs:
            if isinstance(ir, Binary) and BinaryType.return_bool(ir.type):
                for var in ir.read:
                    if is_dependent(var, SolidityVariableComposed('block.timestamp'), func.contract):
                        ret.add(node)
                    if is_dependent(var, SolidityVariable('now'), func.contract):
                        ret.add(node)
    return list(ret)


def _detect_dangerous_timestamp(contract: Contract) -> List[Tuple[Function, List[Node]]]:
    """
    Args:
        contract (Contract)
    Returns:
        list((Function), (list (Node)))
    """
    ret = []
    for f in [f for f in contract.functions if f.contract_declarer == contract]:
        nodes = _timestamp(f)
        if nodes:
            ret.append((f, nodes))
    return ret


class Timestamp(AbstractDetector):
    """
    """

    ARGUMENT = 'timestamp'
    HELP = 'Dangerous usage of `block.timestamp`'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#block-timestamp'

    WIKI_TITLE = 'Block timestamp'
    WIKI_DESCRIPTION = 'Dangerous usage of `block.timestamp`. `block.timestamp` can be manipulated by miners.'
    WIKI_EXPLOIT_SCENARIO = '''"Bob's contract relies on `block.timestamp` for its randomness. Eve is a miner and manipulates `block.timestamp` to exploit Bob's contract.'''
    WIKI_RECOMMENDATION = 'Avoid relying on `block.timestamp`.'

    def _detect(self):
        """
        """
        results = []

        for c in self.contracts:
            dangerous_timestamp = _detect_dangerous_timestamp(c)
            for (func, nodes) in dangerous_timestamp:

                info = [func, " uses timestamp for comparisons\n"]

                info += ['\tDangerous comparisons:\n']
                for node in nodes:
                    info += ['\t- ', node, '\n']

                res = self.generate_result(info)

                results.append(res)

        return results
