from collections import defaultdict
from typing import Dict, List

from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.cfg.node import Node
from slither.core.declarations import Function, Contract, SolidityVariableComposed
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import LowLevelCall, HighLevelCall
from slither.utils.output import Output


def _detect_token_reentrant(contract: Contract) -> Dict[Function, List[Node]]:
    ret: Dict[Function, List[Node]] = defaultdict(list)
    for function in contract.functions_entry_points:
        if function.full_name in [
            "transfer(address,uint256)",
            "transferFrom(address,address,uint256)",
        ]:
            for ir in function.all_slithir_operations():
                if isinstance(ir, (LowLevelCall, HighLevelCall)):
                    if not function.parameters:
                        continue
                    if any(
                        (
                            is_dependent(ir.destination, parameter, function)
                            for parameter in function.parameters
                        )
                    ):
                        ret[function].append(ir.node)
                    if is_dependent(
                        ir.destination, SolidityVariableComposed("msg.sender"), function
                    ):
                        ret[function].append(ir.node)
                    if is_dependent(
                        ir.destination, SolidityVariableComposed("tx.origin"), function
                    ):
                        ret[function].append(ir.node)
    return ret


class TokenReentrancy(AbstractDetector):
    ARGUMENT = "token-reentrancy"
    HELP = "Tokens that are reentrancies unsafe"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#token-reentrant"

    WIKI_TITLE = "Token reentrant"

    # region wiki_description
    WIKI_DESCRIPTION = """
    Tokens that allow arbitrary external call on transfer/transfer (such as ERC223/ERC777) can be exploited on third
    party through a reentrancy."""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
    ```solidity
contract MyToken{
    function transferFrom(address from, address to, uint) public{
        // do some stuff
        from.call("..")
        // do some stuff
    }
}

contract MyDefi{
    function convert(ERC token) public{
        // do some stuff
        token.transferFrom(..)
        //
    }
}
    ```

    `MyDefi` has a reentrancy, but its developers did not think transferFrom could be reentrancy.
    `MyToken` is used in MyDefi. As a result an attacker can exploit the reentrancy."""
    # endregion wiki_exploit_scenario

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """Avoid to have external calls in `transfer`/`transferFrom`.
If you do, ensure your users are aware of the potential issues."""
    # endregion wiki_recommendation

    def _detect(self) -> List[Output]:
        results = []
        for contract in self.compilation_unit.contracts_derived:
            vulns = _detect_token_reentrant(contract)
            for function, nodes in vulns.items():
                info: DETECTOR_INFO = [function, " is an reentrancy unsafe token function:\n"]
                for node in nodes:
                    info += ["\t-", node, "\n"]
                json = self.generate_result(info)
                results.append(json)

        return results
