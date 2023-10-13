from typing import List

from slither.core.cfg.node import Node
from slither.core.declarations import Contract
from slither.core.declarations.function import Function
from slither.core.solidity_types import Type
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import LowLevelCall, HighLevelCall
from slither.analyses.data_dependency.data_dependency import is_tainted
from slither.utils.output import Output


class ReturnBomb(AbstractDetector):

    ARGUMENT = "return-bomb"
    HELP = "A low level callee may consume all callers gas unexpectedly."
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#return-bomb"

    WIKI_TITLE = "Return Bomb"
    WIKI_DESCRIPTION = "A low level callee may consume all callers gas unexpectedly."
    WIKI_EXPLOIT_SCENARIO = """
```solidity
//Modified from https://github.com/nomad-xyz/ExcessivelySafeCall
contract BadGuy {
    function youveActivateMyTrapCard() external pure returns (bytes memory) {
        assembly{
            revert(0, 1000000)
        }
    }
}

contract Mark {
    function oops(address badGuy) public{
        bool success;
        bytes memory ret;

        // Mark pays a lot of gas for this copy
        //(success, ret) = badGuy.call{gas:10000}(
        (success, ret) = badGuy.call(
            abi.encodeWithSelector(
                BadGuy.youveActivateMyTrapCard.selector
            )
        );

        // Mark may OOG here, preventing local state changes
        //importantCleanup();
    }
}

```
After Mark calls BadGuy bytes are copied from returndata to memory, the memory expansion cost is paid. This means that when using a standard solidity call, the callee can "returnbomb" the caller, imposing an arbitrary gas cost. 
Callee unexpectedly makes the caller OOG. 
"""

    WIKI_RECOMMENDATION = "Avoid unlimited implicit decoding of returndata."

    @staticmethod
    def is_dynamic_type(ty: Type) -> bool:
        # ty.is_dynamic ?
        name = str(ty)
        if "[]" in name or name in ("bytes", "string"):
            return True
        return False

    def get_nodes_for_function(self, function: Function, contract: Contract) -> List[Node]:
        nodes = []
        for node in function.nodes:
            for ir in node.irs:
                if isinstance(ir, (HighLevelCall, LowLevelCall)):
                    if not is_tainted(ir.destination, contract):  # type:ignore
                        # Only interested if the target address is controlled/tainted
                        continue

                    if isinstance(ir, HighLevelCall) and isinstance(ir.function, Function):
                        # in normal highlevel calls return bombs are _possible_
                        # if the return type is dynamic and the caller tries to copy and decode large data
                        has_dyn = False
                        if ir.function.return_type:
                            has_dyn = any(
                                self.is_dynamic_type(ty) for ty in ir.function.return_type
                            )

                        if not has_dyn:
                            continue

                    # If a gas budget was specified then the
                    # user may not know about the return bomb
                    if ir.call_gas is None:
                        # if a gas budget was NOT specified then the caller
                        # may already suspect the call may spend all gas?
                        continue

                    nodes.append(node)
                # TODO: check that there is some state change after the call

        return nodes

    def _detect(self) -> List[Output]:
        results = []

        for contract in self.compilation_unit.contracts:
            for function in contract.functions_declared:
                nodes = self.get_nodes_for_function(function, contract)
                if nodes:
                    info: DETECTOR_INFO = [
                        function,
                        " tries to limit the gas of an external call that controls implicit decoding\n",
                    ]

                    for node in sorted(nodes, key=lambda x: x.node_id):
                        info += ["\t", node, "\n"]

                    res = self.generate_result(info)
                    results.append(res)

        return results
