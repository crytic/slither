from typing import List

from slither.analyses.data_dependency.data_dependency import is_tainted
from slither.core.cfg.node import Node
from slither.core.declarations.function_contract import FunctionContract
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import LowLevelCall
from slither.utils.output import Output


def controlled_delegatecall(function: FunctionContract) -> List[Node]:
    ret = []
    for node in function.nodes:
        for ir in node.irs:
            if isinstance(ir, LowLevelCall) and ir.function_name in [
                "delegatecall",
                "callcode",
            ]:
                if is_tainted(ir.destination, function.contract):
                    ret.append(node)
    return ret


class ControlledDelegateCall(AbstractDetector):

    ARGUMENT = "controlled-delegatecall"
    HELP = "Controlled delegatecall destination"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#controlled-delegatecall"

    WIKI_TITLE = "Controlled Delegatecall"
    WIKI_DESCRIPTION = "`Delegatecall` or `callcode` to an address controlled by the user."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Delegatecall{
    function delegate(address to, bytes data){
        to.delegatecall(data);
    }
}
```
Bob calls `delegate` and delegates the execution to his malicious contract. As a result, Bob withdraws the funds of the contract and destructs it."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Avoid using `delegatecall`. Use only trusted destinations."

    def _detect(self) -> List[Output]:
        results = []

        for contract in self.compilation_unit.contracts_derived:
            for f in contract.functions:
                # If its an upgradeable proxy, do not report protected function
                # As functions to upgrades the destination lead to too many FPs
                if contract.is_upgradeable_proxy and f.is_protected():
                    continue
                nodes = controlled_delegatecall(f)
                if nodes:
                    func_info: DETECTOR_INFO = [
                        f,
                        " uses delegatecall to a input-controlled function id\n",
                    ]

                    for node in nodes:
                        node_info: DETECTOR_INFO = func_info + ["\t- ", node, "\n"]
                        res = self.generate_result(node_info)
                        results.append(res)

        return results
