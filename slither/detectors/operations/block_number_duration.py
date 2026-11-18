"""
Module detecting durations written as block counts or time units mixed with block.number
"""

from slither.analyses.data_dependency.data_dependency import is_dependent, KEY_NON_SSA
from slither.core.cfg.node import Node
from slither.core.declarations import Contract, FunctionContract
from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.literal import Literal
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import Assignment, Binary, BinaryType
from slither.slithir.variables.constant import Constant
from slither.utils.output import Output

TIME_SUBDENOMINATIONS = {"seconds", "minutes", "hours", "days", "weeks", "years"}
BLOCK_COUNT_THRESHOLD = 200_000

ARITHMETIC_TYPES = {
    BinaryType.ADDITION,
    BinaryType.SUBTRACTION,
    BinaryType.MULTIPLICATION,
    BinaryType.DIVISION,
}

MIXING_TYPES = {
    BinaryType.ADDITION,
    BinaryType.SUBTRACTION,
    BinaryType.MULTIPLICATION,
    BinaryType.DIVISION,
    BinaryType.LESS,
    BinaryType.GREATER,
    BinaryType.LESS_EQUAL,
    BinaryType.GREATER_EQUAL,
    BinaryType.EQUAL,
    BinaryType.NOT_EQUAL,
}


def _get_duration_from_literal_or_constant(val_obj: object) -> str | None:
    if isinstance(val_obj, Constant):
        if val_obj.subdenomination in TIME_SUBDENOMINATIONS:
            return f"time unit ({val_obj.original_value} {val_obj.subdenomination})"
        if isinstance(val_obj.value, int) and val_obj.value >= BLOCK_COUNT_THRESHOLD:
            return f"large block count ({val_obj.value})"
        if (
            isinstance(val_obj.value, str)
            and val_obj.value.isdigit()
            and int(val_obj.value) >= BLOCK_COUNT_THRESHOLD
        ):
            return f"large block count ({val_obj.value})"

    if hasattr(val_obj, "expression") and isinstance(val_obj.expression, Literal):
        lit = val_obj.expression
        if lit.subdenomination in TIME_SUBDENOMINATIONS:
            return f"time unit ({lit.value} {lit.subdenomination})"
        val = lit.value
        if isinstance(val, int) and val >= BLOCK_COUNT_THRESHOLD:
            return f"large block count ({val})"
        if isinstance(val, str) and val.isdigit() and int(val) >= BLOCK_COUNT_THRESHOLD:
            return f"large block count ({val})"

    if isinstance(val_obj, Literal):
        if val_obj.subdenomination in TIME_SUBDENOMINATIONS:
            return f"time unit ({val_obj.value} {val_obj.subdenomination})"
        val = val_obj.value
        if isinstance(val, int) and val >= BLOCK_COUNT_THRESHOLD:
            return f"large block count ({val})"
        if isinstance(val, str) and val.isdigit() and int(val) >= BLOCK_COUNT_THRESHOLD:
            return f"large block count ({val})"

    return None


def _get_duration_from_expression(expr: object, visited: set[int] | None = None) -> str | None:
    if visited is None:
        visited = set()
    if expr is None or id(expr) in visited:
        return None
    visited.add(id(expr))

    reason = _get_duration_from_literal_or_constant(expr)
    if reason:
        return reason

    if isinstance(expr, Identifier) and hasattr(expr, "value"):
        reason = _get_duration_from_literal_or_constant(expr.value)
        if reason:
            return reason
        if hasattr(expr.value, "expression") and expr.value.expression:
            reason = _get_duration_from_expression(expr.value.expression, visited)
            if reason:
                return reason

    for sub in getattr(expr, "expressions", []):
        reason = _get_duration_from_expression(sub, visited)
        if reason:
            return reason

    return None


def _get_duration_reason(var: object) -> str | None:
    reason = _get_duration_from_literal_or_constant(var)
    if reason:
        return reason
    if hasattr(var, "expression") and var.expression:
        return _get_duration_from_expression(var.expression)
    return None


def _detect_block_number_duration(
    contract: Contract,
) -> list[tuple[FunctionContract, list[tuple[Node, str]]]]:
    results: list[tuple[FunctionContract, list[tuple[Node, str]]]] = []
    block_number = SolidityVariableComposed("block.number")

    contract_duration_vars: dict[object, str] = {}
    for sv in contract.state_variables:
        r = _get_duration_reason(sv)
        if r:
            contract_duration_vars[sv] = r

    for constructor in [
        f for f in contract.functions if f.is_constructor or f.is_constructor_variables
    ]:
        for node in constructor.nodes:
            if node.expression:
                r = _get_duration_from_expression(node.expression)
                if r:
                    for v in node.variables_written:
                        if v not in contract_duration_vars:
                            contract_duration_vars[v] = r
            for ir in node.irs:
                if isinstance(ir, Assignment):
                    r = contract_duration_vars.get(ir.rvalue) or _get_duration_reason(ir.rvalue)
                    if r and ir.lvalue:
                        contract_duration_vars[ir.lvalue] = r

    for func in [f for f in contract.functions if f.contract_declarer == contract]:
        if func.is_constructor_variables:
            continue

        duration_vars: dict[object, str] = dict(contract_duration_vars)

        for lv in func.local_variables:
            r = _get_duration_reason(lv)
            if r:
                duration_vars[lv] = r

        for node in func.nodes:
            if node.expression:
                r = _get_duration_from_expression(node.expression)
                if r:
                    for v in node.variables_written:
                        if v not in duration_vars:
                            duration_vars[v] = r
            for ir in node.irs:
                if isinstance(ir, Binary) and ir.type in ARITHMETIC_TYPES:
                    for op in (ir.variable_left, ir.variable_right):
                        r = duration_vars.get(op) or _get_duration_reason(op)
                        if r:
                            duration_vars[op] = r
                            if ir.lvalue:
                                duration_vars[ir.lvalue] = r
                elif isinstance(ir, Assignment):
                    r = duration_vars.get(ir.rvalue) or _get_duration_reason(ir.rvalue)
                    if r and ir.lvalue:
                        duration_vars[ir.lvalue] = r

        dep_dict = func.context.get(KEY_NON_SSA, {})
        for var, sources in dep_dict.items():
            if var not in duration_vars:
                for s in sources:
                    if s in duration_vars:
                        duration_vars[var] = duration_vars[s]
                        break

        flagged_nodes: dict[int, tuple[Node, str]] = {}

        for node in func.nodes:
            for ir in node.irs:
                if isinstance(ir, Binary) and ir.type in MIXING_TYPES:
                    left, right = ir.variable_left, ir.variable_right
                    if left is None or right is None:
                        continue
                    left_dep = is_dependent(left, block_number, func) or left == block_number
                    right_dep = is_dependent(right, block_number, func) or right == block_number

                    r_left = duration_vars.get(left) or _get_duration_reason(left)
                    r_right = duration_vars.get(right) or _get_duration_reason(right)

                    if left_dep and r_right and not right_dep:
                        if node.node_id not in flagged_nodes:
                            flagged_nodes[node.node_id] = (node, r_right)
                    elif right_dep and r_left and not left_dep:
                        if node.node_id not in flagged_nodes:
                            flagged_nodes[node.node_id] = (node, r_left)

        if flagged_nodes:
            sorted_nodes = [flagged_nodes[k] for k in sorted(flagged_nodes.keys())]
            results.append((func, sorted_nodes))

    return results


class BlockNumberDuration(AbstractDetector):
    ARGUMENT = "block-number-duration"
    HELP = "Durations written as block counts or time units mixed with block numbers"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#block-number-duration"
    WIKI_TITLE = "Block number duration"
    WIKI_DESCRIPTION = (
        "Durations expressed as block counts or with time units mixed with `block.number`. "
        "Block-denominated durations change wall-clock meaning when chains adjust block times."
    )
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Timelock {
    uint256 public constant LOCK_TIME = 7 days;
    function unlockAt(uint256 startBlock) public view returns (bool) {
        return block.number > startBlock + LOCK_TIME;
    }
}
```
`LOCK_TIME` uses `days` (evaluating to 604,800 seconds) but is added to `block.number`.
If block times are 12 seconds, 604,800 blocks represents ~84 days instead of 7 days.
"""
    WIKI_RECOMMENDATION = (
        "Use `block.timestamp` when measuring durations or time windows. If block numbers are required, "
        "document the assumed block time explicitly."
    )

    def _detect(self) -> list[Output]:
        results: list[Output] = []

        for c in self.contracts:
            for func, node_tuples in _detect_block_number_duration(c):
                info: DETECTOR_INFO = [
                    func,
                    " mixes block numbers with duration literals or long block intervals:\n",
                ]

                for node, reason in node_tuples:
                    info += ["\t- ", node, f" (uses {reason})\n"]

                res = self.generate_result(info)
                results.append(res)

        return results
