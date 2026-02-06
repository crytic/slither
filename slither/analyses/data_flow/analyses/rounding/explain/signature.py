"""DSPy signature and typed output models for rounding trace analysis."""

import dspy
from pydantic import BaseModel, Field


class TraceStep(BaseModel):
    """One step in the rounding trace, with all context together."""

    function_name: str = Field(
        description="The function at this step in the chain",
    )
    condition: str = Field(
        description=(
            "Branch condition to reach this step, or 'always' if unconditional. "
            "Use the actual Solidity expression."
        ),
    )
    inputs: str = Field(
        description=(
            "What values enter this function and where they come from "
            "(e.g., 'bptOut from request.amount, mainBalance from balances[0]')"
        ),
    )
    operation: str = Field(
        description=(
            "The arithmetic that produces the traced rounding direction "
            "(e.g., 'sub(newMainBalance, mainBalance)'), or 'delegates' "
            "if this step just calls the next function"
        ),
    )
    next_call: str = Field(
        description=(
            "Which function is called next in the chain, or 'returns' if this is a leaf"
        ),
    )


class TraceAnalysis(BaseModel):
    """Ordered sequence of steps following one rounding trace path."""

    steps: list[TraceStep] = Field(
        description=(
            "Steps in chain order, from outermost caller to the leaf "
            "operation that produces the traced rounding direction. "
            "Only include steps that lead to the traced_tag direction. "
            "Skip branches that lead to other directions."
        ),
    )


class AnalyzeRoundingTrace(dspy.Signature):
    """Trace one rounding path through a Solidity call chain step by step.

    IMPORTANT: Only follow the path that leads to the traced_tag direction.
    When a function has multiple branches producing different rounding
    directions, only describe the branch that leads to traced_tag.
    Skip steps that produce other directions entirely.

    For each function in the chain, describe the condition that selects
    this path, what values flow in, and what arithmetic produces the
    rounding direction. Organize as an ordered list of steps from
    outermost caller to leaf operation.

    Do NOT assess correctness or security. Only describe the flow.
    """

    trace_chain: str = dspy.InputField(
        desc=(
            "Rounding provenance chain showing function calls and their "
            "rounding tags (UP, DOWN, NEUTRAL, UNKNOWN), as an indented tree"
        ),
    )
    traced_tag: str = dspy.InputField(
        desc=(
            "The specific rounding direction being traced (UP or DOWN). "
            "Only follow paths that produce this direction."
        ),
    )
    solidity_source: str = dspy.InputField(
        desc=(
            "Solidity source code for each function in the trace chain, "
            "separated by === FunctionName === markers"
        ),
    )
    contract_context: str = dspy.InputField(
        desc="Contract name and top-level function being analyzed",
    )
    analysis: TraceAnalysis = dspy.OutputField(
        desc=(
            "Ordered steps following ONLY the traced_tag path from "
            "caller to leaf. Exclude branches leading to other directions."
        ),
    )
