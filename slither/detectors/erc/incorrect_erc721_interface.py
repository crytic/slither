"""
Detect incorrect erc721 interface.
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class IncorrectERC721InterfaceDetection(AbstractDetector):
    """
    Incorrect ERC721 Interface
    """

    ARGUMENT = "erc721-interface"
    HELP = "Incorrect ERC721 interfaces"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-erc721-interface"
    )

    WIKI_TITLE = "Incorrect erc721 interface"
    WIKI_DESCRIPTION = "Incorrect return values for `ERC721` functions. A contract compiled with solidity > 0.4.22 interacting with these functions will fail to execute them, as the return value is missing."
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Token{
    function ownerOf(uint256 _tokenId) external view returns (bool);
    //...
}
```
`Token.ownerOf` does not return an address like `ERC721` expects. Bob deploys the token. Alice creates a contract that interacts with it but assumes a correct `ERC721` interface implementation. Alice's contract is unable to interact with Bob's contract."""

    WIKI_RECOMMENDATION = (
        "Set the appropriate return values and vtypes for the defined `ERC721` functions."
    )

    @staticmethod
    def incorrect_erc721_interface(signature):
        (name, parameters, returnVars) = signature

        # ERC721
        if name == "balanceOf" and parameters == ["address"] and returnVars != ["uint256"]:
            return True
        if name == "ownerOf" and parameters == ["uint256"] and returnVars != ["address"]:
            return True
        if (
            name == "safeTransferFrom"
            and parameters == ["address", "address", "uint256", "bytes"]
            and returnVars != []
        ):
            return True
        if (
            name == "safeTransferFrom"
            and parameters == ["address", "address", "uint256"]
            and returnVars != []
        ):
            return True
        if (
            name == "transferFrom"
            and parameters == ["address", "address", "uint256"]
            and returnVars != []
        ):
            return True
        if name == "approve" and parameters == ["address", "uint256"] and returnVars != []:
            return True
        if name == "setApprovalForAll" and parameters == ["address", "bool"] and returnVars != []:
            return True
        if name == "getApproved" and parameters == ["uint256"] and returnVars != ["address"]:
            return True
        if (
            name == "isApprovedForAll"
            and parameters == ["address", "address"]
            and returnVars != ["bool"]
        ):
            return True

        # ERC165 (dependency)
        if name == "supportsInterface" and parameters == ["bytes4"] and returnVars != ["bool"]:
            return True

        return False

    @staticmethod
    def detect_incorrect_erc721_interface(contract):
        """Detect incorrect ERC721 interface

        Returns:
            list(str) : list of incorrect function signatures
        """

        # Verify this is an ERC721 contract.
        if not contract.is_possible_erc721() or not contract.is_possible_erc20():
            return []

        funcs = contract.functions
        functions = [
            f
            for f in funcs
            if IncorrectERC721InterfaceDetection.incorrect_erc721_interface(f.signature)
        ]
        return functions

    def _detect(self):
        """Detect incorrect erc721 interface

        Returns:
            dict: [contract name] = set(str)  events
        """
        results = []
        for c in self.slither.contracts_derived:
            functions = IncorrectERC721InterfaceDetection.detect_incorrect_erc721_interface(c)
            if functions:
                for function in functions:
                    info = [
                        c,
                        " has incorrect ERC721 function interface:",
                        function,
                        "\n",
                    ]
                    res = self.generate_result(info)

                    results.append(res)

        return results
