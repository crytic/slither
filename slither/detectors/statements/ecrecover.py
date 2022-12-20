"""
Module detecting improper use of ecrecover.

"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Binary, BinaryType
from slither.slithir.operations.solidity_call import SolidityCall


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
    WIKI_RECOMMENDATION = "Check return value of ecrecover and signature contains a nonce"

    def _detect(self):

        results = []

        for contract in self.compilation_unit.contracts:
            for function in contract.functions:
                for call in function.solidity_calls:
                    if call.name == "ecrecover(bytes32,uint8,bytes32,bytes32)":
                        flag = 0
                        for vari in function._variables:
                            if "nonce" in vari.lower():
                                flag = 1
                        if flag == 0:
                            info = [
                                "No nonce check found in ",
                                function,
                                "\n",
                            ]
                            res = self.generate_result(info)
                            results.append(res)
                        flag = 0

                        find_erecovery = 0
                        for node in function.nodes:

                            for ir in node.irs:
                                if find_erecovery == 1:
                                    if isinstance(ir, Binary):
                                        if (ir.type == BinaryType.NOT_EQUAL) or (
                                            ir.type == BinaryType.EQUAL
                                        ):
                                            flag = 1
                                else:
                                    if (
                                        isinstance(ir, SolidityCall)
                                        and ir.function.name
                                        == "ecrecover(bytes32,uint8,bytes32,bytes32)"
                                    ):
                                        find_erecovery = 1
                        if flag == 0:
                            info = [
                                "No return check found in ",
                                function,
                                "\n",
                            ]
                            res = self.generate_result(info)
                            results.append(res)
        return results
