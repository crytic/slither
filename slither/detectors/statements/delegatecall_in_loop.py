from slither.core.cfg.node import NodeType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import LowLevelCall


def detect_delegatecall_in_loop(contract):
    results = []
    for f in contract.functions + contract.modifiers:
        if f.is_implemented and f.payable:
            delegatecall_in_loop(f.entry_point, False, [], results)
    return results


def delegatecall_in_loop(node, in_loop, visited, results):
    if node in visited:
        return
    # shared visited
    visited.append(node)

    if node.type == NodeType.STARTLOOP:
        in_loop = True
    elif node.type == NodeType.ENDLOOP:
        in_loop = False

    if in_loop:
        for ir in node.all_slithir_operations():
            if isinstance(ir, (LowLevelCall)) and ir.function_name == "delegatecall":
                results.append(node)

    for son in node.sons:
        delegatecall_in_loop(son, in_loop, visited, results)


class DelegatecallInLoop(AbstractDetector):
    """
    Detect the use of delegatecall inside a loop in a payable function
    """

    ARGUMENT = "delegatecall-loop"
    HELP = "Payable functions using `delegatecall` inside a loop"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#payable-functions-using-delegatecall-inside-a-loop"

    WIKI_TITLE = "Payable functions using `delegatecall` inside a loop"
    WIKI_DESCRIPTION = """
Detect the use of `delegatecall` inside a loop in a payable function.
It's dangerous because `delegatecall` forward the `msg.value` in case the function called is payable.
"""

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract DelegatecallInLoop{

    mapping (address => uint256) balances;

    function bad(address[] memory receivers) public payable {
        for (uint256 i = 0; i < receivers.length; i++) {
            address(this).delegatecall(abi.encodeWithSignature("addBalance(address)", receivers[i]));
        }
    }

    function addBalance(address a) public payable {
        balances[a] += msg.value;
    } 

}
```
When calling `bad` the same `msg.value` amount will be accredited multiple times."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """
Don't use `delegatecall` inside a loop in a payable function or carefully check that the function called by `delegatecall` is not payable/doesn't use `msg.value`.
"""

    def _detect(self):
        """"""
        results = []
        for c in self.compilation_unit.contracts_derived:
            values = detect_delegatecall_in_loop(c)
            for node in values:
                func = node.function

                info = [func, " has delegatecall inside a loop in a payable function: ", node, "\n"]
                res = self.generate_result(info)
                results.append(res)

        return results
