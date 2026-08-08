"""
Module detecting the transient storage clearing helper collision bug.

See: https://www.soliditylang.org/blog/2026/02/18/transient-storage-clearing-helper-collision-bug/
"""

from slither.core.cfg.node import Node
from slither.core.declarations import Contract
from slither.core.declarations.contract import Contract as ContractDecl
from slither.core.declarations.enum import Enum
from slither.core.declarations.structure import Structure
from slither.core.solidity_types.array_type import ArrayType
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.mapping_type import MappingType
from slither.core.solidity_types.type import Type
from slither.core.solidity_types.type_alias import TypeAlias
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    make_solc_versions,
    DETECTOR_INFO,
)
from slither.slithir.operations import Delete
from slither.slithir.variables.reference import ReferenceVariable
from slither.slithir.variables.state_variable import StateIRVariable
from slither.utils.output import Output


def _resolve_state_variable(
    var: StateIRVariable | StateVariable | ReferenceVariable,
) -> StateVariable | None:
    """
    Return None when the root is not a state variable.

    Resolve a delete lvalue to the underlying StateVariable.
    For ReferenceVariables (from delete mapping[key] or .pop()),
    follows points_to_origin to reach the root.
    """
    if isinstance(var, ReferenceVariable):
        var = var.points_to_origin
    if isinstance(var, StateIRVariable):
        return var.non_ssa_version
    if isinstance(var, StateVariable):
        return var
    return None


def _type_involves_value_type(t: Type) -> bool:
    """
    Return True if clearing t involves clearing a value type.

    Array clearing at slot granularity always involves uint256,
    regardless of element type.  Struct clearing recurses into each
    member.
    """
    if isinstance(t, (ElementaryType, TypeAlias)):
        return True
    if isinstance(t, UserDefinedType):
        if isinstance(t.type, (Enum, ContractDecl)):
            return True
        if isinstance(t.type, Structure):
            return any(
                _type_involves_value_type(m.type)
                for m in t.type.elems_ordered
            )
    if isinstance(t, ArrayType):
        return True
    if isinstance(t, MappingType):
        return _type_involves_value_type(t.type_to)
    return False


def has_persistent_clearing(contract: Contract) -> bool:
    """
    Return True when a contract clears persistent storage of a value type.

    Uses `contract.functions` (including inherited) because the
    two sides of the collision need not be in the same contract.
    """
    for function in contract.functions:
        for node in function.nodes:
            for ir in node.irs:
                if not isinstance(ir, Delete):
                    continue
                state_var = _resolve_state_variable(ir.lvalue)
                if state_var is None or state_var.is_transient:
                    continue
                cleared_type = ir.lvalue.type
                if cleared_type and _type_involves_value_type(
                    cleared_type
                ):
                    return True
    return False


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
                if state_var is None:
                    continue
                if state_var.is_transient:
                    results.append((node, state_var))

    return results


class TransientDelete(AbstractDetector):
    """
    Detect delete operations on transient state variables in contracts
    that also clear persistent storage
    """

    ARGUMENT = "transient-delete"
    HELP = "Detects `delete` on transient state variables (compiler opcode collision bug)"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#transient-delete"
    WIKI_TITLE = "Transient storage delete opcode collision"
    WIKI_DESCRIPTION = (
        "Solidity 0.8.28 through 0.8.33 with `--via-ir` share a "
        "single Yul clearing helper for persistent and transient "
        "storage of the same type. When a contract uses `delete` "
        "on a transient state variable and also clears persistent "
        "storage involving a value type, the compiler may emit the "
        "wrong opcode, silently corrupting persistent storage or "
        "leaving transient state uncleared."
    )

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract OverwriteStorage {
    address public owner;
    mapping(uint256 => address) public delegates;
    address transient _lock;

    constructor() { owner = msg.sender; }

    function clearDelegate(uint256 id) external {
        delete delegates[id];
    }

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
            if not has_persistent_clearing(contract):
                continue
            for node, var in detect_transient_delete_operation(contract):
                info: DETECTOR_INFO = [
                    node,
                    " uses `delete` on transient variable `",
                    var,
                    "`, which may emit the wrong storage opcode if using --via-ir\n",
                ]
                results.append(self.generate_result(info))

        return results
