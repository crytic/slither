"""CLI entry point for rounding direction analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from slither import Slither
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
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    KnownLibraryTags,
    load_known_tags,
)
from slither.analyses.data_flow.logger import get_logger
from slither.core.declarations import Contract, Function
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

TargetMap = dict[str, list[str]]


# ── Argument parsing ─────────────────────────────────────────────


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Rounding direction analysis visualization"
    )
    parser.add_argument(
        "project_path",
        help="Path to Solidity file or project directory",
    )
    parser.add_argument(
        "-c",
        "--contract",
        help="Filter by filename or exact contract name",
    )
    parser.add_argument(
        "-f",
        "--function",
        help="Filter to this specific function name",
    )
    parser.add_argument(
        "--targets",
        metavar="FILE",
        help='JSON {"Contract": ["fn1"], "Other": "*"}',
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all variables including NEUTRAL parameters",
    )
    parser.add_argument(
        "--trace",
        choices=["UP", "DOWN", "UNKNOWN"],
        help="Show provenance chain for this rounding tag",
    )
    _add_explain_arguments(parser)
    return parser


def _add_explain_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    """Add --explain, --safe-libs, and --include-tests flags."""
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Use LM to identify conditions (requires --trace)",
    )
    parser.add_argument(
        "--explain-model",
        default="anthropic/claude-sonnet-4-5-20250929",
        help="DSPy model identifier for --explain",
    )
    parser.add_argument(
        "--safe-libs",
        nargs="?",
        const="__builtin__",
        metavar="FILE",
        help="Trust known library rounding directions",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test/mock contracts (skipped by default)",
    )


# ── Function collection ──────────────────────────────────────────


def _collect_functions(
    slither_instance: Slither,
    contract_filter: Optional[str],
    function_filter: Optional[str],
    include_tests: bool = False,
) -> list[FunctionContract]:
    """Collect functions to analyze based on filters."""
    functions: list[FunctionContract] = []

    for contract in slither_instance.contracts:
        if contract.is_test and not include_tests:
            continue

        if contract_filter:
            if not _contract_matches_filter(
                contract,
                contract_filter,
            ):
                continue
            function_source = contract.functions_declared
        else:
            function_source = contract.functions

        for function in function_source:
            if function_filter and function.name != function_filter:
                continue
            if isinstance(function, FunctionContract) and function.is_implemented:
                functions.append(function)

    return functions


def _contract_matches_filter(
    contract: Contract,
    contract_filter: str,
) -> bool:
    """Check if a contract matches the filter."""
    if contract.name == contract_filter:
        return True
    contract_file = (
        contract.source_mapping.filename.short if contract.source_mapping else ""
    )
    return contract_filter in contract_file


def _collect_functions_from_targets(
    slither_instance: Slither,
    target_map: TargetMap,
    include_tests: bool = False,
) -> list[FunctionContract]:
    """Collect functions matching a targets map."""
    functions: list[FunctionContract] = []
    for contract in slither_instance.contracts:
        if contract.is_test and not include_tests:
            continue
        if contract.name not in target_map:
            continue

        allowed = target_map[contract.name]
        for function in contract.functions_declared:
            if not isinstance(function, FunctionContract):
                continue
            if not function.is_implemented:
                continue
            if allowed and function.name not in allowed:
                continue
            functions.append(function)

    return functions


# ── Validation and loading ───────────────────────────────────────


def _validate_target_args(
    args: argparse.Namespace,
) -> None:
    """Validate --targets is not combined with -c or -f."""
    if args.targets and (args.contract or args.function):
        logger.error_and_raise(
            "--targets cannot be combined with -c/--contract or -f/--function",
            ValueError,
        )


def _validate_explain_args(
    args: argparse.Namespace,
) -> None:
    """Validate --explain flag requirements."""
    if not args.explain:
        return
    if not args.trace:
        logger.error_and_raise(
            "--explain requires --trace to be set",
            ValueError,
        )
    if not EXPLAIN_AVAILABLE:
        logger.error_and_raise(
            "DSPy is required for --explain. "
            "Install with: pip install slither-analyzer[explain]",
            ImportError,
        )


def _setup_explain(
    args: argparse.Namespace,
) -> Optional[TraceExplainer]:
    """Configure DSPy and create explainer if active."""
    if not args.explain:
        return None
    configure_dspy(model=args.explain_model)
    return TraceExplainer()


def _build_lookup_from_functions(
    functions: list[FunctionContract],
) -> dict[str, Function]:
    """Build function name lookup from analyzed functions."""
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


def _load_targets(
    targets_arg: Optional[str],
) -> Optional[TargetMap]:
    """Load target contract/function map from a JSON file."""
    if targets_arg is None:
        return None
    file_path = Path(targets_arg)
    if not file_path.exists():
        logger.error_and_raise(
            f"targets file not found: {file_path}",
            FileNotFoundError,
        )
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        logger.error_and_raise(
            f"targets file must be a JSON object, got {type(raw).__name__}",
            ValueError,
        )
    return _parse_target_map(raw)


def _parse_target_map(raw: dict) -> TargetMap:
    """Validate and normalize the raw targets JSON."""
    targets: TargetMap = {}
    for contract, functions in raw.items():
        if functions == "*":
            targets[contract] = []
            continue
        if not isinstance(functions, list):
            logger.error_and_raise(
                f"Invalid value for '{contract}': "
                f'expected list or "*", '
                f"got {type(functions).__name__}",
                ValueError,
            )
        targets[contract] = [str(fn) for fn in functions]
    return targets


def _load_safe_libs(
    safe_libs_arg: Optional[str],
) -> Optional[KnownLibraryTags]:
    """Load known library tags from --safe-libs argument."""
    if safe_libs_arg is None:
        return None
    if safe_libs_arg == "__builtin__":
        return load_known_tags()
    file_path = Path(safe_libs_arg)
    if not file_path.exists():
        logger.error_and_raise(
            f"safe-libs file not found: {file_path}",
            FileNotFoundError,
        )
    return load_known_tags(file_path)


def _parse_trace_tag(
    trace_arg: Optional[str],
) -> Optional[RoundingTag]:
    """Parse --trace argument into RoundingTag."""
    tag_map = {
        "UP": RoundingTag.UP,
        "DOWN": RoundingTag.DOWN,
        "UNKNOWN": RoundingTag.UNKNOWN,
    }
    if trace_arg is None:
        return None
    return tag_map.get(trace_arg)


# ── Orchestration ────────────────────────────────────────────────


def _resolve_functions(
    args: argparse.Namespace,
) -> list[FunctionContract]:
    """Parse Solidity project and collect target functions."""
    project_path = Path(args.project_path)
    if not project_path.exists():
        logger.error_and_raise(
            f"Path not found: {project_path}",
            FileNotFoundError,
        )

    target_map = _load_targets(args.targets)
    slither_instance = Slither(str(project_path))
    include_tests = args.include_tests

    if target_map is not None:
        return _collect_functions_from_targets(
            slither_instance,
            target_map,
            include_tests,
        )
    return _collect_functions(
        slither_instance,
        args.contract,
        args.function,
        include_tests,
    )


def _run_analyses(
    functions: list[FunctionContract],
    *,
    show_all: bool,
    known_tags: Optional[KnownLibraryTags],
) -> list[AnnotatedFunction]:
    """Run rounding analysis on each function."""
    results: list[AnnotatedFunction] = []
    for function in functions:
        try:
            results.append(
                analyze_function(
                    function,
                    show_all=show_all,
                    known_tags=known_tags,
                )
            )
        except Exception as exception:
            logger.error(f"Error analyzing {function.name}: {exception}")
    return results


def main() -> None:
    """Main entry point."""
    parser = _create_argument_parser()
    args = parser.parse_args()

    _validate_explain_args(args)
    _validate_target_args(args)

    functions = _resolve_functions(args)
    if not functions:
        logger.warning("No functions found to analyze")
        return

    explainer = _setup_explain(args)
    known_tags = _load_safe_libs(args.safe_libs)
    function_lookup: Optional[dict[str, Function]] = None
    if explainer is not None:
        function_lookup = _build_lookup_from_functions(functions)

    analyses = _run_analyses(
        functions,
        show_all=args.all,
        known_tags=known_tags,
    )
    if not analyses:
        logger.warning("No functions analyzed successfully")
        return

    trace_tag = _parse_trace_tag(args.trace)
    for analysis in analyses:
        display_annotated_source(analysis)
        if trace_tag is not None:
            display_trace_section(
                analysis,
                trace_tag,
                explainer,
                function_lookup,
            )

    if len(analyses) > 1:
        display_summary_table(analyses)


if __name__ == "__main__":
    main()
