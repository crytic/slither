"""
Module detecting the transient storage clearing helper collision bug.

See: https://www.soliditylang.org/blog/2026/02/18/transient-storage-clearing-helper-collision-bug/
"""

from slither.core.cfg.node import Node
from slither.core.declarations import Contract
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    make_solc_versions,
    DETECTOR_INFO,
)
from slither.slithir.operations import Delete
from slither.slithir.variables.state_variable import StateIRVariable
from slither.utils.output import Output


def _resolve_state_variable(
    var: StateIRVariable | StateVariable,
) -> StateVariable:
    """Follow IR indirections back to the declared StateVariable."""
    if isinstance(var, StateIRVariable):
        return var.non_ssa_version
    return var


def detect_transient_delete_operation(
    contract: Contract,
) -> list[tuple[Node, StateVariable]]:
    """Return (node, state_var) for every `delete` of a transient var."""
    results: list[tuple[Node, StateVariable]] = []
    for function in contract.functions_declared:
        for node in function.nodes:
            for ir in node.irs:
                if not isinstance(ir, Delete):
                    continue
                state_var = _resolve_state_variable(ir.lvalue)
                if state_var.is_transient:
                    results.append((node, state_var))

    return results


class TransientDelete(AbstractDetector):
    """
    Detect delete operations on transient state variables
    """

    ARGUMENT = "transient-delete"
    HELP = "Detects `delete` on transient state variables (compiler opcode collision bug)"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#transient-delete"
    WIKI_TITLE = "Transient storage delete opcode collision"
    WIKI_DESCRIPTION = (
        "Solidity 0.8.28 through 0.8.33 with `--via-ir` share a single "
        "Yul clearing helper for persistent and transient storage of the "
        "same type. Using `delete` on a transient state variable can "
        "cause the compiler to emit `sstore` instead of `tstore` (or "
        "vice-versa), silently corrupting persistent storage or leaving "
        "transient state uncleared."
    )

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract OverwriteStorage {
    address transient _lock;

    function guarded() external {
        require(_lock == address(0), "locked");
        _lock = msg.sender;
        // ... protected logic ...
        delete _lock;
    }
}
```"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        "Ensure you are not using --via-ir with solc 0.8.28 through 0.8.33, "
        "if so, use compiler version >= 0.8.34 or replace `delete <transient_var>` "
        "with an explicit zero assignment."
    )

    VULNERABLE_SOLC_VERSIONS = make_solc_versions(8, 28, 33)

    def _detect(self) -> list[Output]:
        results: list[Output] = []

        for contract in self.compilation_unit.contracts_derived:
            for node, var in detect_transient_delete_operation(contract):
                info: DETECTOR_INFO = [
                    node,
                    " uses `delete` on transient variable `",
                    var,
                    "`, which may emit the wrong storage opcode if using --via-ir\n",
                ]
                results.append(self.generate_result(info))

        return results
