"""
Module detecting improper use of ecrecover.

"""
from collections import defaultdict
from typing import DefaultDict, List, Tuple, Union
from slither.utils.output import Output
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.declarations.function_contract import FunctionContract
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.assignment import Assignment
from slither.core.expressions.expression import Expression
from slither.core.expressions.call_expression import CallExpression
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.local_variable import LocalVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import Binary, BinaryType
from slither.slithir.operations.solidity_call import SolidityCall
from slither.analyses.data_dependency.data_dependency import is_tainted


class Ecrecover(AbstractDetector):
    """
    Detect improper use of ecrecover
    """

    ARGUMENT = "ecrecover"
    HELP = "Return value of ecrecover is not checked. And Signature does not contain a nonce."
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.LOW

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#ecrecover"
    WIKI_TITLE = "ECRECOVER"
    WIKI_DESCRIPTION = "ECRECOVER"
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract A {
    struct Info {
        uint tokenId;
        address owner;
        // uint nonce
    }
    uint maxBreed = 5;
    mapping (uint => mapping(uint => address)) list;
    mapping (uint => uint) count;
    function mint(uint tokenId, address addr) internal {
        require(count[tokenId] < maxBreed, "");
        list[tokenId][count[tokenId]] = addr;
        count[tokenId]++;
    }
    function verify(Info calldata info, uint8 v, bytes32 r, bytes32 s) external {
        bytes32 hash = keccak256(abi.encode(info));
        bytes32 data =
            keccak256(
                abi.encodePacked("\x19Ethereum Signed Message:\n32", hash)
            );
        address receiver = ecrecover(data, v, r, s);
        // require(signer != address(0), "ECDSA: invalid signature");
        mint(info.tokenId, receiver);
    }
}
```
First, signature does not contain nonce.   
Second, there is no verification of ecrecover's return value.   
"""
    WIKI_RECOMMENDATION = (
        "Check the return value of ecrecover and ensure that the signed data contains a nonce"
    )

    def _detect(self) -> List[Output]:
        results = []

        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions_and_modifiers_declared:
                var_results, nonce_results = _detect_ecrecover(function)
                for _, var_nodes in var_results:
                    for var, nodes in var_nodes.items():
                        info: DETECTOR_INFO = [
                            var,
                            " lacks a zero-check on ",
                            ":\n",
                        ]
                        for node in nodes:
                            info += ["\t\t- ", node, "\n"]
                        res = self.generate_result(info)
                        results.append(res)
                for _, nonce_nodes in nonce_results:
                    for var, nodes in nonce_nodes.items():
                        info: DETECTOR_INFO = [
                            var,
                            " lacks a nonce on ",
                            ":\n",
                        ]
                        print("NODES", nodes)
                        for node in nodes:
                            info += ["\t\t- ", node, "\n"]
                        res = self.generate_result(info)
                        results.append(res)

        return results


def _zero_address_validation(var: LocalVariable, function: Function) -> bool:
    for node in function.nodes:
        if node.contains_if() or node.contains_require_or_assert():
            for ir in node.irs:
                expression = str(ir.expression)
                if isinstance(ir, Binary) and str(var) in expression:
                    if (
                        ir.type == BinaryType.NOT_EQUAL or ir.type == BinaryType.EQUAL
                    ) and "address(0)" in expression:
                        return True
    return False


def _nonce_validation(function: Function) -> bool:
    for node in function.nodes:
        if "nonce" in node.variables_written:
            return True
    return False


def _detect_ecrecover(
    function: Function,
) -> Tuple[
    List[Tuple[Function, DefaultDict[LocalVariable, List[Node]]]],
    List[Tuple[Function, DefaultDict[LocalVariable, List[Node]]]],
]:
    results = []
    nonce_results = []

    if SolidityFunction("ecrecover(bytes32,uint8,bytes32,bytes32)") in function.solidity_calls:
        address_list = []
        nonce_list = []
        var_nodes = defaultdict(list)
        nonce_nodes = defaultdict(list)
        for node in function.nodes:
            if SolidityFunction("ecrecover(bytes32,uint8,bytes32,bytes32)") in node.solidity_calls:
                for var in node.local_variables_written:
                    if "ecrecover(bytes32,uint8,bytes32,bytes32)" in str(var.expression):
                        address_list.append(var)
                        var_nodes[var].append(node)
            if SolidityFunction("keccak256(bytes)") in node.solidity_calls:
                for var in node.variables_written:
                    if "nonce" not in str(var.expression) and "keccak256" in str(var.expression):
                        if var not in nonce_list:
                            nonce_list.append(var)
                        nonce_nodes[var].append(node)

        for var in address_list:
            if not _zero_address_validation(var, function):
                results.append((function, var_nodes))
        for var in nonce_list:
            if not _nonce_validation(function):
                nonce_results.append((function, nonce_nodes))
    return (results, nonce_results)
