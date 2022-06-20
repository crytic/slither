"""
    Module detecting usages of send and transfer for ETH transfers
"""
from typing import List

from slither.core.cfg.node import Node
from slither.core.declarations import Function, Contract
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import (
    Send,
    Transfer,
)


# pylint: disable=too-many-nested-blocks,too-many-branches
from slither.utils.output import Output


def use_send_or_transfer(func: Function):
    ret: List[Node] = []
    for node in func.nodes:
        for ir in node.irs:
            if isinstance(ir, (Transfer, Send)):
                ret.append(node)

    return ret


def detect_send_or_transfer(contract: Contract):
    """
        Detect usages of send or transfer
    Args:
        contract (Contract)
    Returns:
        list((Function), (list (Node)))
    """
    ret = []
    for f in [f for f in contract.functions if f.contract_declarer == contract]:
        nodes = use_send_or_transfer(f)
        if nodes:
            ret.append((f, nodes))
    return ret


class UnsafeTransfer(AbstractDetector):
    """
    Reference: https://solidity-by-example.org/sending-ether/
    """
    ARGUMENT = "unsafe-transfer"
    HELP = "Functions that send Ether using send or transfer"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation"

    WIKI_TITLE = "Functions that send Ether using send or transfer"
    WIKI_DESCRIPTION = "Unsafe call to a function sending Ether by using send or transfer. Use call instead."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract UnsafeTransfer{
    address destination;
    function setDestination(){
        destination = msg.sender;
    }
    function withdraw(uint256 amount) public{
        destination.transfer(amount);
    }
}
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Use call for ETH transfer as it is now the recommended way instead of send or transfer"

    def _detect(self) -> List[Output]:
        """"""
        results = []

        for c in self.contracts:
            unsafe_transfer_result = detect_send_or_transfer(c)
            for (func, nodes) in unsafe_transfer_result:

                info = [func, " uses `transfer` or `send` for ETH transfer\n"]
                info += ["\tDangerous calls:\n"]

                # sort the nodes to get deterministic results
                nodes.sort(key=lambda x: x.node_id)

                for node in nodes:
                    # print(node)
                    info += ["\t- ", node, "\n"]

                res = self.generate_result(info)

                results.append(res)

        return results