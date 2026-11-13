"""
Module detecting durations written as block counts or time units mixed with block.number
"""

from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.cfg.node import Node
from slither.core.declarations import Contract, FunctionContract
from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.core.expressions.literal import Literal
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import Binary
from slither.slithir.variables.constant import Constant
from slither.utils.output import Output

TIME_SUBDENOMINATIONS = {"seconds", "minutes", "hours", "days", "weeks", "years"}
BLOCK_COUNT_THRESHOLD = 200_000


def _get_duration_reason(var: object) -> str | None:
    if isinstance(var, Constant):
        if var.subdenomination in TIME_SUBDENOMINATIONS:
            return f"time unit ({var.original_value} {var.subdenomination})"
        if isinstance(var.value, int) and var.value >= BLOCK_COUNT_THRESHOLD:
            return f"large block count ({var.value})"
        if (
            isinstance(var.value, str)
            and var.value.isdigit()
            and int(var.value) >= BLOCK_COUNT_THRESHOLD
        ):
            return f"large block count ({var.value})"

    if hasattr(var, "expression") and isinstance(var.expression, Literal):
        if var.expression.subdenomination in TIME_SUBDENOMINATIONS:
            return f"time unit ({var.expression.value} {var.expression.subdenomination})"
        val = var.expression.value
        if isinstance(val, int) and val >= BLOCK_COUNT_THRESHOLD:
            return f"large block count ({val})"
        if isinstance(val, str) and val.isdigit() and int(val) >= BLOCK_COUNT_THRESHOLD:
            return f"large block count ({val})"

    return None


def _detect_block_number_duration(
    contract: Contract,
) -> list[tuple[FunctionContract, list[tuple[Node, str]]]]:
    results: list[tuple[FunctionContract, list[tuple[Node, str]]]] = []
    block_number = SolidityVariableComposed("block.number")

    for func in [f for f in contract.functions if f.contract_declarer == contract]:
        flagged_nodes: dict[int, tuple[Node, str]] = {}

        for node in func.nodes:
            has_block_number = any(is_dependent(v, block_number, node) for v in node.variables_read)
            if not has_block_number:
                continue

            for ir in node.irs:
                if isinstance(ir, Binary):
                    for operand in (ir.variable_left, ir.variable_right):
                        reason = _get_duration_reason(operand)
                        if reason and node.node_id not in flagged_nodes:
                            flagged_nodes[node.node_id] = (node, reason)

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
