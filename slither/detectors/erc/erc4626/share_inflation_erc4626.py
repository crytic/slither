"""
Detects ERC4626 vaults vulnerable to share inflation attacks
"""
from typing import List, Tuple

from slither.analyses.data_dependency.data_dependency import (
    is_dependent,
)
from slither.core.cfg.node import Node
from slither.core.variables.variable import Variable
from slither.utils.output import Output
from slither.core.variables.state_variable import StateVariable
from slither.core.declarations import SolidityVariable, FunctionContract, Contract
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Binary, BinaryType, HighLevelCall


def _get_balanceof_this_variables(contract) -> List[Variable]:
    """
    Returns a list of variables that are populated by external contract.balanceOf(address(this)) calls.
    """
    variables = []
    for function in contract.functions:
        for node in function.nodes:
            for ir in node.irs:
                # high level call filter prevents address(this).balanceOf() inclusion
                if (
                    isinstance(ir, HighLevelCall)
                    and ir.function.signature_str == "balanceOf(address) returns(uint256)"
                    and is_dependent(ir.arguments[0], SolidityVariable("this"), contract)
                ):
                    variables.append(ir.lvalue)
    return variables


def _get_variables_from_add_operations(contract) -> List[Variable]:
    """
    Returns a list of variables that are calculated from addition operations.
    """
    add_src_vars = []
    for function in contract.functions:
        if function.is_shadowed:
            continue
        for node in function.nodes:
            for ir in node.irs:
                if not isinstance(ir, Binary):
                    continue
                if not ir.type == BinaryType.ADDITION:
                    continue
                add_src_vars.append(ir.lvalue)
    return add_src_vars


def _locate_variable_writes(contract, variable) -> List[Node]:
    """
    Returns a list of nodes from the provided contract that write to the specified variable.
    """
    writes = []
    for function in contract.functions:
        if function.is_shadowed:
            continue
        for node in function.nodes:
            if variable in node.variables_written:
                writes.append(node)
    return writes


def _is_contract_eligible_for_detector(contract) -> bool:
    if not contract.is_erc4626():
        return False
    if contract.is_abstract:
        return False
    return True


def _detect_share_inflation_attack_erc4626(
    contract,
) -> List[Tuple[Contract, FunctionContract, FunctionContract]]:
    """
    Given a contract, locate share inflation attacks and return the results
    """
    results = []

    # generate a list of variables generated via add operations
    variables_from_add_ops = _get_variables_from_add_operations(contract)

    # generate a list of variables from asset.balanceOf(address(this)) expressions
    variables_from_balanceof_this = _get_balanceof_this_variables(contract)

    # mint/deposit functions, find return value
    for function in contract.functions:
        if function.signature_str not in [
            "deposit(uint256,address) returns(uint256)",
            "mint(uint256,address) returns(uint256)",
        ]:
            continue

        # Determine whether the return value is influenced by asset.balanceOf(this). Such a relationship
        # implies the amount of shares minted is influenceable by vault donations.
        # Vaults that keep track of their accounting in a dedicated variable and do not support donations are not
        # impacted by this attack.
        balanceof_dependency_match = None
        for balance_of_variable in variables_from_balanceof_this:
            if is_dependent(function.returns[0], balance_of_variable, contract):
                balanceof_dependency_match = balance_of_variable
                break
        if not balanceof_dependency_match:
            continue

        # A contract implementing the OZ mitigation will have two addition dependencies,
        # one for the numerator and one for the denominator (in the price per share calculation).
        # See this thread for details on their mitigation:
        # https://ethereum-magicians.org/t/address-eip-4626-inflation-attacks-with-virtual-shares-and-assets/12677

        # One nice thing about this "two-addition" heuristic is that vaults that implement fees but fail to
        # implement mitigation will likely only have one addition operation, hopefully reducing false negatives.
        parent_addition_operations = 0
        for addition_operation in variables_from_add_ops:
            # mitigation is very unlikely to happen through a storage variable
            if isinstance(addition_operation, StateVariable):
                continue

            if is_dependent(function.returns[0], addition_operation, contract):
                parent_addition_operations += 1

        if parent_addition_operations >= 2:
            continue

        results.append((contract, balanceof_dependency_match.function, function))
    return results


class DetectERC4626ShareInflation(AbstractDetector):
    """
    ERC4626 Share Inflation Attack Detector
    """

    ARGUMENT = "share-inflation-erc4626"
    HELP = "ERC4626 Share Inflation Vulnerability"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#share-inflation-erc4626"

    WIKI_TITLE = "ERC4626 Share Inflation Vulnerability"
    WIKI_DESCRIPTION = """The vault's ability to recognize profit can be tampered with using vault donations.
    This allows an attacker to front run initial vault deposits and steal a victim's deposit."""

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
Consider a newly deployed ERC4626 vault that uses a price-per-share(PPS) accounting mechanism.
The first deposit into the vault must use special logic to determine how many shares should be minted because the PPS ratio cannot be calculated when there are zero vault shares outstanding.
An exploitable implementation may assume the initial PPS ratio to be 1:1, so an initial deposit of 5 ether will mint 5e18 wei of shares:

```solidity
contract VaultImpl is IERC4626{
	function deposit(uint256 assets, address receiver) public returns (uint256) {
	    [...]
        if(totalSupply() == 0 and totalAssets() == 0){
            // mint same number of shares as assets received
            uint256 sharesToMint = assets;
            _mint(receiver, sharesToMint);
        } else {
            // calculate price per share to figure out amount to mint
            uint256 sharesToMint = assets * totalSupply() / totalAssets();
            _mint(receiver, sharesToMint);
        }
    }

    function totalAssets() returns (uint256) {
        return asset.balanceOf(address(this));
    }

    [...]
}
```

- Attacker Alice monitors the mempool for the first transaction that will deposit into the vault.
- Victim Bob submits a deposit transaction to the mempool that will deposit two asset tokens into the vault (1e18 wei).
- Alice detects the transaction and front runs it with the following two transactions:
    - The first transaction deposits 1 wei of asset token in to the vault. One wei of shares is minted for Alice.
    - The second transaction transfers 1e18 wei of asset token to the vault. 
        - The vault's totalAssets is now 1+1e18 wei.
        - The vault's PPS is now 1+1e18 wei: 1 wei (aka 1+1e18 asset tokens are required to receive 1 wei of share token)
- Bob's deposit of 1e18 wei is executed, but the entire amount of their deposit is only worth 0.9999999 wei of share tokens. This amount is rounded down towards zero.
- Alice now redeems her 1 wei of shares and receives her vault donation in addition to Bob's entire deposit.
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """
Use a dedicated variable to track the vault's totalAssets to prevent vault donations from being recognized as profit.

Alternately, use a higher precision for tracking vault shares as is described here: https://ethereum-magicians.org/t/address-eip-4626-inflation-attacks-with-virtual-shares-and-assets/12677
"""

    def _format_results(
        self, unformatted_results: List[Tuple[Contract, FunctionContract, FunctionContract]]
    ) -> List[Output]:
        formatted_results = []

        for contract, balanceof_function, deposit_function in unformatted_results:
            # Give them the node where asset.balanceOf(this) happens & trace it to the end of deposit/mint.
            info = [
                deposit_function,
                " is dependent on asset.balanceOf(this) to determine deposit/mint credits, enabling share inflation attacks:\n",
            ]

            info += ["\tSource: ", balanceof_function, ": \n"]
            for node in balanceof_function.nodes[1:]:
                info += ["\t- ", node, "\n"]

            return_value_writes = _locate_variable_writes(contract, deposit_function.returns[0])

            info += ["\tTarget: ", deposit_function, ": \n"]
            for node in return_value_writes:
                info += ["\t- ", node, "\n"]
            res = self.generate_result(info)
            formatted_results.append(res)
        return formatted_results

    def _detect(self):
        """
        Detect ERC4626 share inflation attacks
        """
        results = []

        for contract in self.contracts:
            if not _is_contract_eligible_for_detector(contract):
                continue
            results.extend(_detect_share_inflation_attack_erc4626(contract))

        return self._format_results(results)
