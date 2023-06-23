from typing import List, Dict, Tuple
from slither.core.declarations.contract import Contract
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.slithir.operations.operation import Operation
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import SolidityCall
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.utils.output import Output


class UsingEcrecover(AbstractDetector):
    """
    Detect calls to abi.encodeWithSelector that may result in unexpected calldata encodings
    """

    ARGUMENT = "using-ecrecover"
    HELP = "The use of ecrecover can be unsafe"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/trailofbits/slither/wiki/using-ecrecover"
    WIKI_TITLE = "The use of ecrecover can be unsafe"
    WIKI_DESCRIPTION = "Detects if a contract uses ecrecover for signature validation."
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract UsingEcrecover {
    mapping(uint256 => address) guardian;

    function checkSignature(uint256 guardIndex, uint256 amount, bytes32 hash, uint8 v, bytes32 r, bytes32 s) public {
        address signer = ecrecover(hash, v, r, s);
        require(signer == guardian[guardIndex]);
        (bool success,) = msg.sender.call{value: amount}("");
        require(success);
    }
}

```
The contract allows any signature to be considered valid since ecrecover returns address(0) on invalid signatures, which the function does not check.
"""
    WIKI_RECOMMENDATION = (
        "Use a library like OpenZeppelin's ECDSA to ensure important safety checks are performed."
    )

    def _detect(self) -> List[Output]:
        results = []
        for contract in self.compilation_unit.contracts_derived:
            for func, node in check_contract(contract):
                info = [
                    func,
                    " uses ecrecover: ",
                    node,
                ]
                json = self.generate_result(info)
                results.append(json)

        return results


def check_using_ecrecover(
    function: Function, node: Node, ir: Operation
) -> List[Tuple[Function, Node]]:
    result = []
    if isinstance(ir, SolidityCall) and ir.function == SolidityFunction(
        "ecrecover(bytes32,uint8,bytes32,bytes32)"
    ):
        result.append((function, node))

    return result


def check_contract(contract: Contract) -> List[Tuple[Function, Node]]:
    """Check contract's usage of ecrecover"""
    result = []
    for function in contract.functions_and_modifiers_declared:
        if SolidityFunction("ecrecover(bytes32,uint8,bytes32,bytes32)") in function.solidity_calls:
            for node in function.nodes:
                if (
                    SolidityFunction("ecrecover(bytes32,uint8,bytes32,bytes32)")
                    in node.solidity_calls
                ):
                    for ir in node.irs:
                        result += check_using_ecrecover(function, node, ir)

    return result
