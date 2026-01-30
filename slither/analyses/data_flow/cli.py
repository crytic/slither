"""CLI entry point for data flow analysis."""

import argparse
import sys
from pathlib import Path

from slither.analyses.data_flow.display import console

# Default timeout for Optimize queries (milliseconds)
# 500ms is needed for correct results on 256-bit inequality constraints
DEFAULT_OPTIMIZE_TIMEOUT_MS = 500


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(description="Slither Data Flow Analysis")
    parser.add_argument(
        "--test", "-t", action="store_true",
        help="Run automated tests using pytest with snapshot testing"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show extra details during analysis",
    )
    parser.add_argument(
        "--debug", "-d", action="store_true",
        help="Show detailed debugging information"
    )
    parser.add_argument(
        "--embed", action="store_true",
        help="Enable IPython embed on errors for interactive debugging",
    )
    parser.add_argument(
        "--contract", "-c", type=str, default=None,
        help="Path to contract file or project directory for verbose mode",
    )
    parser.add_argument(
        "--contracts-dir", type=str, default=None,
        help="Directory containing .sol files for test mode or project directory",
    )
    parser.add_argument(
        "--show", "-s", type=str, metavar="CONTRACT_FILE",
        help="Show verbose table output for a specific contract file",
    )
    parser.add_argument(
        "--function", "-f", type=str, metavar="FUNCTION_NAME",
        help="Filter to a specific function name (use with --show or --contract)",
    )
    parser.add_argument(
        "--contract-name", type=str, metavar="CONTRACT_NAME",
        help="Filter to a specific contract name (e.g., 'Settlement')",
    )
    parser.add_argument(
        "--skip-compile", action="store_true",
        help="Skip compilation step (use existing build artifacts)",
    )
    parser.add_argument(
        "--timeout", type=int, default=DEFAULT_OPTIMIZE_TIMEOUT_MS, metavar="MS",
        help=f"Timeout in ms for SMT optimization (default: {DEFAULT_OPTIMIZE_TIMEOUT_MS})",
    )
    parser.add_argument(
        "--skip-range-solving", action="store_true",
        help="Skip SMT optimization for ranges and use conservative type bounds",
    )
    parser.add_argument(
        "--telemetry", action="store_true",
        help="Show solver telemetry (operation counts and timings)",
    )
    parser.add_argument(
        "--update-snapshots", action="store_true",
        help="Update pytest snapshots with current analysis results (use with --test)",
    )
    parser.add_argument(
        "path", nargs="?", type=str,
        help="Optional path to contract file or project directory",
    )
    return parser


def _run_tests(args: argparse.Namespace) -> int:
    """Run tests using pytest with snapshot testing."""
    import subprocess

    cmd = ["pytest", "slither/analyses/data_flow/tests/", "-v"]
    if args.update_snapshots:
        cmd.append("--snapshot-update")
    if args.path:
        cmd.extend(["-k", args.path])
    return subprocess.call(cmd)


def _run_show_mode(args: argparse.Namespace) -> int:
    """Show verbose output for a specific test."""
    from slither.analyses.data_flow.verbose import show_test_output

    contracts_dir = args.contracts_dir or "../contracts/src"
    show_test_output(args.show, function_name=args.function, contracts_dir=contracts_dir)
    return 0


def _resolve_contract_path(args: argparse.Namespace) -> str:
    """Resolve the contract path from CLI arguments."""
    # Priority: positional argument > --contract > --contracts-dir > default
    if args.path:
        contract_path = args.path
    elif args.contract:
        contract_path = args.contract
    elif args.contracts_dir:
        contract_path = args.contracts_dir
    else:
        contract_path = "../contracts/src/FunctionArgs.sol"

    contract_path_obj = Path(contract_path)
    if contract_path_obj.exists():
        return str(contract_path_obj.resolve())

    console.print(f"[yellow]Warning: Path may not exist: {contract_path}[/yellow]")
    console.print("[dim]Slither will attempt to detect project type[/dim]")
    return contract_path


def _run_verbose_mode(args: argparse.Namespace) -> int:
    """Run verbose mode analysis."""
    from slither.analyses.data_flow.verbose import run_verbose, VerboseConfig

    contract_path = _resolve_contract_path(args)
    config = VerboseConfig(
        debug=args.debug,
        function_name=args.function,
        contract_name=args.contract_name,
        embed=args.embed,
        skip_compile=args.skip_compile,
        timeout_ms=args.timeout,
        skip_range_solving=args.skip_range_solving,
        show_telemetry=args.telemetry,
    )
    run_verbose(contract_path, config)
    return 0


def main() -> int:
    """Main entry point with command-line argument handling."""
    parser = _create_argument_parser()
    args = parser.parse_args()

    if args.test:
        return _run_tests(args)
    elif args.show:
        return _run_show_mode(args)
    else:
        return _run_verbose_mode(args)


if __name__ == "__main__":
    sys.exit(main())
