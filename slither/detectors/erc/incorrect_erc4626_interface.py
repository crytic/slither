"""
Detect incorrect ERC 4626 interface.
"""
from typing import List
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output


class IncorrectERC4626InterfaceDetection(AbstractDetector):
    """
    Incorrect ERC4626 interface.
    """
    ARGUMENT = "erc4626-interface"
    HELP = "Incorrect ERC4626 interface"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = ("")  # Todo

    WIKI_TITLE = "Incorrect ERC4626 interface"
    WIKI_DESCRIPTION = "Incorrect signatures and return types for `ERC 4626` functions. A contract compiled with solidity > 0.4.22 interacting with these functions would fail to execute them, as a result of incorrect parameter or return value(s) types."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
    ```solidity
    contract Vault {
        function deposit(uint256 assets, address receiver) external returns(bool);
        //...
    };
    ```
    `Vault.deposit` does not return `uint256 {shares}` like `ERC4626` expects. Bob deploys the vault, Alice creates a contract that interacts with it but assumes a correct `ERC4626` implementation. Alice's contract is unable to interact with bob's contract."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        "set the appropriate return values and vtypes for the defined `ERC4626` functions."
    )

    @staticmethod
    def incorrect_erc4626_interface(signature):
        (name, parameters, returnVars) = signature

        # ERC4626
        if name == "asset" and parameters == [] and returnVars != ["address"]:
            return True
        if name == "totalAssets" and parameters == [] and returnVars != ["uint256"]:
            return True
        if name == "convertToShares" and parameters == ["uint256"] and returnVars != ["uint256"]:
            return True
        if name == "convertToAssets" and parameters == ["uint256"] and returnVars != ["uint256"]:
            return True
        if name == "maxDeposit" and parameters == ["address"] and returnVars != ["uint256"]:
            return True
        if name == "previewDeposit" and parameters == ["uint256"] and returnVars != ["uint256"]:
            return True
        if name == "deposit" and parameters == ["uint256", "address"] and returnVars != ["uint256"]:
            return True
        if name == "maxMint" and parameters == ["address"] and returnVars != ["uint256"]:
            return True
        if name == "previewMint" and parameters == ["uint256"] and returnVars != ["uint256"]:
            return True
        if name == "mint" and parameters == ["uint256", "address"] and returnVars != ["uint256"]:
            return True
        if name == "maxWithdraw" and parameters == ["address"] and returnVars != ["uint256"]:
            return True
        if name == "previewWithdraw" and parameters == ["uint256"] and returnVars != ["uint256"]:
            return True
        if name == "withdraw" and parameters == ["uint256", "address", "address"] and returnVars != ["uint256"]:
            return True
        if name == "maxRedeem" and parameters == ["address"] and returnVars != ["uint256"]:
            return True
        if name == "previewRedeem" and parameters == ["uint256"] and returnVars != ["uint256"]:
            return True
        if name == "redeem" and parameters == ["uint256", "address", "address"] and returnVars != ["uint256"]:
            return True

    @staticmethod
    def detect_incorrect_erc4626_interface(contract):
        """
        Detect incorrect ERC4626 interface

        Returns:
            list(str) : list of incorrect function signatures
        """
        # verify this is an ERC4626 contract
        if not contract.is_erc4626():
            return []
        funcs = contract.functions

        functions = [
            f
            for f in funcs
            if IncorrectERC4626InterfaceDetection.incorrect_erc4626_interface(f.signature)
        ]

        return functions

    def _detect(self) -> List[Output]:
        """Detect incorrect ERC4626 interface

            Returns:
                dict: [contract name] = set(str)  events
        """
        results = []
        for c in self.compilation_unit.contracts_derived:
            functions = IncorrectERC4626InterfaceDetection.detect_incorrect_erc4626_interface(c)
            if functions:
                for function in functions:
                    info = [
                        c,
                        " has incorrect ERC4626 function interface:",
                        function,
                        "\n",
                    ]
                    res = self.generate_result(info)
                    results.append(res)
        return results
