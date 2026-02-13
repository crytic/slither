"""Detector for rounding direction inconsistencies in arithmetic."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from slither.analyses.data_flow.analyses.rounding.annotate import (
    analyze_function,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingTag,
)
from slither.analyses.data_flow.analyses.rounding.display import (
    display_annotated_source,
    display_summary_table,
    display_trace_section,
)
from slither.analyses.data_flow.analyses.rounding.models import (
    AnnotatedFunction,
    RoundingFinding,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    KnownLibraryTags,
    load_known_tags,
)
from slither.analyses.data_flow.logger import get_logger
from slither.detectors.abstract_detector import (
    DETECTOR_INFO,
    AbstractDetector,
    DetectorClassification,
)
from slither.utils.output import Output

if TYPE_CHECKING:
    from slither.core.declarations import Function
    from slither.core.declarations.function_contract import FunctionContract

try:
    from slither.analyses.data_flow.analyses.rounding.explain.configuration import (
        configure_dspy,
    )
    from slither.analyses.data_flow.analyses.rounding.explain.explainer import (
        TraceExplainer,
        build_function_lookup,
    )

    EXPLAIN_AVAILABLE = True
except ImportError:
    EXPLAIN_AVAILABLE = False

logger = get_logger()

# ── Tag string → enum lookup ──────────────────────────

_TAG_MAP: dict[str, RoundingTag] = {
    "UP": RoundingTag.UP,
    "DOWN": RoundingTag.DOWN,
    "NEUTRAL": RoundingTag.NEUTRAL,
    "UNKNOWN": RoundingTag.UNKNOWN,
}


class RoundingInconsistency(AbstractDetector):
    """Detect conflicting rounding directions in arithmetic."""

    ARGUMENT = "rounding-inconsistency"
    HELP = "Rounding direction inconsistencies in arithmetic"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = (
        "https://github.com/crytic/slither/wiki/"
        "Detector-Documentation#rounding-inconsistency"
    )
    WIKI_TITLE = "Rounding inconsistency"
    WIKI_DESCRIPTION = (
        "Detects conflicting rounding directions in arithmetic "
        "operations that may lead to value extraction."
    )
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Vault {
    function withdraw(uint shares, uint supply, uint total)
        external returns (uint assets)
    {
        // UP: rounds in user's favor
        uint numerator = shares * total;
        // DOWN: Solidity floor division rounds against user
        assets = numerator / supply;
        // Conflict: numerator biased UP, division biased DOWN
    }
}
```
An attacker can exploit the inconsistency to extract more value
than entitled by choosing inputs that maximize the gap between
the upward-biased numerator and the downward-biased division.
"""
    WIKI_RECOMMENDATION = (
        "Ensure consistent rounding direction across related "
        "arithmetic operations within each function."
    )
    STANDARD_JSON = False

    # ── Configuration flags ─────────────────────────
    # Edit these directly to control detector behavior.
    TRACE_TAG: Optional[str] = None
    EXPLAIN: bool = False
    EXPLAIN_MODEL: str = "anthropic/claude-sonnet-4-5-20250929"
    SAFE_LIBS: Optional[str] = None
    SHOW_ALL: bool = False

    def _detect(self) -> List[Output]:
        results: List[Output] = []
        known_tags = _load_safe_libs(self.SAFE_LIBS)
        explainer = _setup_explain(self.EXPLAIN, self.EXPLAIN_MODEL)
        trace_tag = (
            _TAG_MAP.get(self.TRACE_TAG) if self.TRACE_TAG else None
        )

        self.analyses: list[AnnotatedFunction] = []
        analyzed_functions: list[FunctionContract] = []

        for contract in self.contracts:
            for function in contract.functions_and_modifiers_declared:
                if not function.is_implemented:
                    continue
                annotated = _analyze_single_function(
                    function, self.SHOW_ALL, known_tags
                )
                if annotated is None:
                    continue

                self.analyses.append(annotated)
                analyzed_functions.append(function)
                _display_function(
                    annotated, trace_tag, explainer,
                    analyzed_functions,
                )
                results.extend(
                    _collect_results(self, annotated, function)
                )

        if len(self.analyses) > 1:
            display_summary_table(self.analyses)

        return results


# ── Helpers ───────────────────────────────────────


def _display_function(
    annotated: AnnotatedFunction,
    trace_tag: Optional[RoundingTag],
    explainer: Optional[TraceExplainer],
    analyzed_functions: list[FunctionContract],
) -> None:
    """Display annotated source and optional trace section."""
    display_annotated_source(annotated)
    if trace_tag is None:
        return
    function_lookup = _build_lookup(analyzed_functions)
    display_trace_section(
        annotated, trace_tag, explainer, function_lookup,
    )


def _collect_results(
    detector: AbstractDetector,
    annotated: AnnotatedFunction,
    function: FunctionContract,
) -> list[Output]:
    """Collect finding outputs from a single analyzed function."""
    results: list[Output] = []
    results.extend(
        _build_finding_outputs(
            detector, annotated.inconsistencies, function,
        )
    )
    results.extend(
        _build_finding_outputs(
            detector, annotated.annotation_mismatches, function,
        )
    )
    return results


def _analyze_single_function(
    function: FunctionContract,
    show_all: bool,
    known_tags: Optional[KnownLibraryTags],
) -> Optional[AnnotatedFunction]:
    """Run rounding analysis on a single function."""
    try:
        return analyze_function(
            function, show_all=show_all, known_tags=known_tags,
        )
    except Exception as exc:
        logger.error(f"Error analyzing {function.name}: {exc}")
        return None


def _build_finding_outputs(
    detector: AbstractDetector,
    findings: list[RoundingFinding],
    function: FunctionContract,
) -> list[Output]:
    """Build Output objects from a list of RoundingFindings."""
    outputs: list[Output] = []
    for finding in findings:
        info: DETECTOR_INFO = [
            function,
            ": ",
            finding.message,
            "\n",
            "\t- ",
            finding.node,
            "\n",
        ]
        outputs.append(detector.generate_result(info))
    return outputs


def _load_safe_libs(
    safe_libs_arg: Optional[str],
) -> Optional[KnownLibraryTags]:
    """Load known library tags from configuration."""
    if safe_libs_arg is None:
        return None
    if safe_libs_arg == "__builtin__":
        return load_known_tags()
    file_path = Path(safe_libs_arg)
    if not file_path.exists():
        logger.error(
            f"safe-libs file not found: {file_path}"
        )
        return None
    return load_known_tags(file_path)


def _setup_explain(
    explain_enabled: bool,
    model: str,
) -> Optional[TraceExplainer]:
    """Configure DSPy and create explainer if enabled."""
    if not explain_enabled:
        return None
    if not EXPLAIN_AVAILABLE:
        logger.error(
            "DSPy is required for EXPLAIN. "
            "Install with: pip install slither-analyzer[explain]"
        )
        return None
    configure_dspy(model=model)
    return TraceExplainer()


def _build_lookup(
    functions: list[FunctionContract],
) -> dict[str, Function]:
    """Build function name lookup from analyzed functions."""
    if not EXPLAIN_AVAILABLE:
        return {}
    all_functions: list[Function] = []
    seen_contracts: set[str] = set()
    for function in functions:
        if not function.contract:
            continue
        contract_name = function.contract.name
        if contract_name in seen_contracts:
            continue
        seen_contracts.add(contract_name)
        all_functions.extend(function.contract.functions)
    return build_function_lookup(all_functions)
