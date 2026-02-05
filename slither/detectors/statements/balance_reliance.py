"""
Detector for potentially unsafe uses of address.balance.

Detects:
1. Strict equality comparisons (== or !=) with address.balance
2. Assignment of address.balance to state variables

These patterns are problematic because:
- Attackers can forcibly send ETH using selfdestruct
- Pre-calculated contract addresses can receive ETH before deployment
- Balance can change between transactions unpredictably

Related to issue #2778.
"""

from __future__ import annotations

from slither.analyses.data_dependency.data_dependency import is_dependent_ssa
from slither.core.cfg.node import Node
from slither.core.declarations import Function
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import (
    Assignment,
    Binary,
    BinaryType,
    SolidityCall,
)
from slither.slithir.variables.temporary_ssa import TemporaryVariableSSA
from slither.slithir.variables.local_variable import LocalIRVariable
from slither.utils.output import Output


class BalanceReliance(AbstractDetector):
    """
    Detects potentially unsafe uses of address.balance:
    1. Strict equality comparisons (== or !=)
    2. Assignment to state variables
    """

    ARGUMENT = "balance-reliance"
    HELP = "Dangerous reliance on address.balance"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#balance-reliance"
    WIKI_TITLE = "Dangerous reliance on address.balance"

    WIKI_DESCRIPTION = """
Detects potentially unsafe uses of `address.balance`:
1. Strict equality comparisons (`==` or `!=`) - An attacker can forcibly send ETH using `selfdestruct`, breaking equality assumptions.
2. Assignment to state variables - Storing balance values leads to stale data and incorrect assumptions."""

    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Crowdsale {
    uint256 public savedBalance;

    function fund_reached() public returns(bool) {
        // BAD: strict equality can be manipulated
        return address(this).balance == 100 ether;
    }

    function saveBalance() public {
        // BAD: balance can change, making stored value stale
        savedBalance = address(this).balance;
    }
}
```
An attacker can use `selfdestruct` to forcibly send ETH to the contract, making `fund_reached()` return false even after 100 ETH is collected. Similarly, `savedBalance` becomes stale immediately after being set."""

    WIKI_RECOMMENDATION = """
Use range checks instead of strict equality for balance comparisons:
```solidity
// GOOD: use >= for minimum balance checks
require(address(this).balance >= 100 ether, "Insufficient balance");

// GOOD: use range checks
require(address(this).balance >= minAmount && address(this).balance <= maxAmount);
```
Avoid storing balance in state variables. If needed, recalculate on each use."""

    # Only applicable to Solidity
    LANGUAGE = "solidity"

    def _find_balance_taints(
        self, functions: list[FunctionContract]
    ) -> list[LocalIRVariable | TemporaryVariableSSA]:
        """
        Find all variables that hold address.balance values.
        """
        taints = []
        for func in functions:
            for node in func.nodes:
                for ir in node.irs_ssa:
                    if isinstance(ir, SolidityCall) and ir.function == SolidityFunction(
                        "balance(address)"
                    ):
                        taints.append(ir.lvalue)
        return taints

    def _is_tainted(
        self,
        var,
        taints: list[LocalIRVariable | TemporaryVariableSSA],
        contract: Contract,
    ) -> bool:
        """Check if a variable is tainted by address.balance."""
        for taint in taints:
            if is_dependent_ssa(var, taint, contract):
                return True
        return False

    def _detect_strict_equality(
        self,
        functions: list[FunctionContract],
        taints: list[LocalIRVariable | TemporaryVariableSSA],
        contract: Contract,
    ) -> list[tuple[FunctionContract, Node, str]]:
        """
        Detect strict equality comparisons (== or !=) with balance-tainted values.
        """
        results = []
        for func in functions:
            if isinstance(func, FunctionTopLevel):
                continue
            for node in func.nodes:
                for ir in node.irs_ssa:
                    if isinstance(ir, Binary) and ir.type in (
                        BinaryType.EQUAL,
                        BinaryType.NOT_EQUAL,
                    ):
                        # Check if either operand is tainted by balance
                        left_tainted = self._is_tainted(ir.variable_left, taints, contract)
                        right_tainted = self._is_tainted(ir.variable_right, taints, contract)
                        if left_tainted or right_tainted:
                            op = "==" if ir.type == BinaryType.EQUAL else "!="
                            results.append((func, node, f"strict equality ({op})"))
        return results

    def _detect_state_assignment(
        self,
        functions: list[FunctionContract],
        taints: list[LocalIRVariable | TemporaryVariableSSA],
        contract: Contract,
    ) -> list[tuple[FunctionContract, Node, str]]:
        """
        Detect assignment of balance-tainted values to state variables.
        """
        results = []
        for func in functions:
            if isinstance(func, FunctionTopLevel):
                continue
            for node in func.nodes:
                for ir in node.irs_ssa:
                    if isinstance(ir, Assignment):
                        # Check if assigning to a state variable
                        if isinstance(ir.lvalue, StateVariable) or (
                            hasattr(ir.lvalue, "non_ssa_version")
                            and isinstance(ir.lvalue.non_ssa_version, StateVariable)
                        ):
                            # Check if the value being assigned is tainted
                            if self._is_tainted(ir.rvalue, taints, contract):
                                results.append((func, node, "state variable assignment"))
        return results

    def _detect(self) -> list[Output]:
        results = []

        for contract in self.compilation_unit.contracts_derived:
            functions = contract.all_functions_called + contract.modifiers

            # Find all balance taints
            taints = self._find_balance_taints(functions)
            if not taints:
                continue

            # Detect strict equality comparisons
            equality_issues = self._detect_strict_equality(functions, taints, contract)

            # Detect state variable assignments
            assignment_issues = self._detect_state_assignment(functions, taints, contract)

            # Combine and report
            all_issues = equality_issues + assignment_issues

            for func, node, issue_type in all_issues:
                info: DETECTOR_INFO = [
                    func,
                    f" uses address.balance in {issue_type}:\n",
                    "\t- ",
                    node,
                    "\n",
                ]
                results.append(self.generate_result(info))

        return results
