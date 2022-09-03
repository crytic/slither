"""
Module detecting EIP-2612 domain separator collision
"""
from slither.utils.function import get_function_id
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.solidity_types.elementary_type import ElementaryType


class DomainSeparatorCollision(AbstractDetector):
    """
    Domain separator collision
    """

    ARGUMENT = "domain-separator-collision"
    HELP = "Detects ERC20 tokens that have a function whose signature collides with EIP-2612's DOMAIN_SEPARATOR()"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#domain-separator-collision"
    )

    WIKI_TITLE = "Domain separator collision"
    WIKI_DESCRIPTION = "An ERC20 token has a function whose signature collides with EIP-2612's DOMAIN_SEPARATOR(), causing unanticipated behavior for contracts using `permit` functionality."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Contract{
    function some_collisions() external() {}
}
```
`some_collision` clashes with EIP-2612's DOMAIN_SEPARATOR() and will interfere with contract's using `permit`."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Remove or rename the function that collides with DOMAIN_SEPARATOR()."

    def _detect(self):
        domain_sig = get_function_id("DOMAIN_SEPARATOR()")
        for contract in self.compilation_unit.contracts_derived:
            if contract.is_erc20():
                for func in contract.functions_entry_points + contract.state_variables:
                    # Skip internal and private variables
                    if func.solidity_signature is None:
                        continue
                    # External/ public function names should not collide with DOMAIN_SEPARATOR()
                    hash_collision = (
                        func.solidity_signature != "DOMAIN_SEPARATOR()"
                        and get_function_id(func.solidity_signature) == domain_sig
                    )
                    # DOMAIN_SEPARATOR() should return bytes32
                    incorrect_return_type = (
                        func.solidity_signature == "DOMAIN_SEPARATOR()"
                        and func.return_type[0] != ElementaryType("bytes32")
                    )
                    if hash_collision or incorrect_return_type:
                        info = [
                            "The function signature of ",
                            func,
                            " collides with DOMAIN_SEPARATOR and should be renamed or removed.\n",
                        ]
                        res = self.generate_result(info)
                        return [res]
        return []
