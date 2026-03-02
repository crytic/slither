"""RoundingCLI — CLI and programmatic entry point for rounding analysis."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from slither.analyses.data_flow.analyses.rounding.core.models import (
    AnnotatedFunction,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingTag,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    KnownLibraryTags,
    load_known_tags,
)
from slither.analyses.data_flow.analyses.rounding.output.annotate import (
    analyze_function,
)
from slither.analyses.data_flow.analyses.rounding.output.display import (
    display_annotated_source,
    display_summary_table,
    display_trace_section,
)
from slither.analyses.data_flow.analyses.rounding.output.serialize import (
    RoundingResult,
    RoundingSummary,
    TraceNodeDict,
    serialize_annotated_function,
    serialize_trace_node,
    summarize_annotated_function,
)
from slither.analyses.data_flow.registry.abstract_analysis import (
    AbstractAnalysis,
)
from slither.core.slither_core import SlitherCore

_TAG_MAP: dict[str, RoundingTag] = {
    "UP": RoundingTag.UP,
    "DOWN": RoundingTag.DOWN,
    "UNKNOWN": RoundingTag.UNKNOWN,
}


@dataclass(frozen=True, slots=True)
class Target:
    """A filter target: contract name with optional function name."""

    contract: str
    function: str | None


def _parse_targets(raw: str | None) -> list[Target] | None:
    """Parse comma-separated 'Contract' or 'Contract.func' targets."""
    if raw is None:
        return None
    targets: list[Target] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "." in part:
            contract, function = part.split(".", 1)
            targets.append(Target(contract, function))
        else:
            targets.append(Target(part, None))
    return targets or None


def _matches_target(
    contract_name: str,
    function_name: str,
    targets: list[Target],
) -> bool:
    """Check if a contract/function pair matches any target filter."""
    for target in targets:
        if target.contract != contract_name:
            continue
        if target.function is None or target.function == function_name:
            return True
    return False


class RoundingCLI(AbstractAnalysis[RoundingResult, RoundingSummary]):
    """Rounding direction analysis with trace provenance.

    Detects rounding inconsistencies and annotates every variable
    with its rounding direction tag (UP, DOWN, NEUTRAL, UNKNOWN).
    """

    ARGUMENT: ClassVar[str] = "rounding"
    HELP: ClassVar[str] = (
        "Rounding direction analysis with trace provenance"
    )

    def __init__(
        self,
        trace_tag: RoundingTag | None = None,
        known_tags: KnownLibraryTags | None = None,
        show_all: bool = False,
        targets: list[Target] | None = None,
    ) -> None:
        self.trace_tag = trace_tag
        self.known_tags = known_tags
        self.show_all = show_all
        self.targets = targets
        self.results: list[AnnotatedFunction] = []

    @classmethod
    def register_arguments(
        cls,
        group: argparse._ArgumentGroup,
    ) -> None:
        """Register --rounding-* CLI flags."""
        group.add_argument(
            "--rounding-trace",
            choices=["UP", "DOWN", "UNKNOWN"],
            default=None,
            help="Show tag provenance traces for this direction",
        )
        group.add_argument(
            "--rounding-safe-libs",
            nargs="?",
            const="__builtin__",
            default=None,
            help="JSON file with known library tags (or builtin)",
        )
        group.add_argument(
            "--rounding-show-all",
            action="store_true",
            default=False,
            help="Show annotations for all variables (including params)",
        )
        group.add_argument(
            "--rounding-target",
            nargs="?",
            default=None,
            help=(
                "Comma-separated Contract or Contract.function targets"
            ),
        )

    @classmethod
    def from_args(
        cls,
        args: argparse.Namespace,
    ) -> RoundingCLI:
        """Create instance from parsed CLI arguments."""
        trace_tag = _TAG_MAP.get(args.rounding_trace or "")
        known_tags = _load_safe_libs_from_arg(args.rounding_safe_libs)
        targets = _parse_targets(args.rounding_target)
        return cls(
            trace_tag=trace_tag,
            known_tags=known_tags,
            show_all=args.rounding_show_all,
            targets=targets,
        )

    def run(self, slither: SlitherCore) -> None:
        """Run rounding analysis on implemented functions."""
        for contract in slither.contracts:
            for func in contract.functions_and_modifiers_declared:
                if not func.is_implemented:
                    continue
                if self.targets is not None and not _matches_target(
                    contract.name, func.name, self.targets
                ):
                    continue
                annotated = analyze_function(
                    func, self.show_all, self.known_tags
                )
                self.results.append(annotated)

    def display(self) -> None:
        """Display results with Rich formatting."""
        for annotated in self.results:
            display_annotated_source(annotated)
            if self.trace_tag is not None:
                display_trace_section(annotated, self.trace_tag)
        if len(self.results) > 1:
            display_summary_table(self.results)

    def serialize(self) -> list[RoundingResult]:
        """Full results for CLI ``--json`` output."""
        return [
            serialize_annotated_function(result)
            for result in self.results
        ]

    def summarize(self) -> list[RoundingSummary]:
        """Lightweight summaries for MCP ProjectFacts."""
        return [
            summarize_annotated_function(result)
            for result in self.results
        ]

    def get_traces(
        self,
        function_name: str,
        variable_name: str,
        max_depth: int = 10,
    ) -> TraceNodeDict | None:
        """Get a serialized trace for a specific variable."""
        for result in self.results:
            if result.function_name != function_name:
                continue
            trace = result.traces.get(variable_name)
            if trace is None:
                return None
            return serialize_trace_node(trace, max_depth)
        return None


def _load_safe_libs_from_arg(
    safe_libs_arg: str | None,
) -> KnownLibraryTags | None:
    """Convert --rounding-safe-libs argument to KnownLibraryTags."""
    if safe_libs_arg is None:
        return None
    if safe_libs_arg == "__builtin__":
        return load_known_tags()
    return load_known_tags(Path(safe_libs_arg))
