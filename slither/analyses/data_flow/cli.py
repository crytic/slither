"""CLI entry point for data flow analysis."""

import sys
from pathlib import Path

from slither.analyses.data_flow.display import console

# Default timeout for Optimize queries (milliseconds)
DEFAULT_OPTIMIZE_TIMEOUT_MS = 10  # Aggressive timeout for faster analysis


def main() -> int:
    """Main entry point with command-line argument handling."""
    import argparse

    parser = argparse.ArgumentParser(description="Slither Data Flow Analysis Test Suite")
    parser.add_argument(
        "--test", "-t", action="store_true", help="Run automated tests against expected results"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Run in verbose mode (original behavior) or show extra test details",
    )
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Show detailed debugging information"
    )
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Enable IPython embed on errors for interactive debugging",
    )
    parser.add_argument(
        "--contract",
        "-c",
        type=str,
        default=None,
        help="Path to contract file or project directory for verbose mode (Slither supports Foundry, Hardhat, etc.)",
    )
    parser.add_argument(
        "--contracts-dir",
        type=str,
        default=None,
        help="Directory containing .sol files for test mode, or project directory for verbose mode if --contract not specified",
    )
    parser.add_argument(
        "--show",
        "-s",
        type=str,
        metavar="CONTRACT_FILE",
        help="Show verbose table output for a specific contract file (e.g., FunctionArgs.sol)",
    )
    parser.add_argument(
        "--function",
        "-f",
        type=str,
        metavar="FUNCTION_NAME",
        help="Filter to a specific function name (use with --show or --contract)",
    )
    parser.add_argument(
        "--contract-name",
        type=str,
        metavar="CONTRACT_NAME",
        help="Filter to a specific contract name (e.g., 'Settlement'). Only analyzes the specified contract.",
    )
    parser.add_argument(
        "--generate-expected",
        "-g",
        action="store_true",
        help="Generate expected results from current analysis output (for copying into expected_results.py). "
        "If a contract file name is provided as positional argument, only generates results for that file.",
    )
    parser.add_argument(
        "--skip-compile",
        action="store_true",
        help="Skip compilation step (use existing build artifacts). "
        "Much faster if project is already compiled.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_OPTIMIZE_TIMEOUT_MS,
        metavar="MS",
        help=f"Timeout in milliseconds for each SMT optimization query (default: {DEFAULT_OPTIMIZE_TIMEOUT_MS}). "
        "Lower values = faster but less precise ranges. Higher values = more precise but slower.",
    )
    parser.add_argument(
        "--skip-range-solving",
        action="store_true",
        help="Skip SMT optimization for ranges and use conservative type bounds instead. "
        "Much faster but produces wider (less precise) ranges.",
    )
    parser.add_argument(
        "--telemetry",
        action="store_true",
        help="Show solver telemetry (operation counts and timings) at the end of analysis. "
        "Useful for profiling and identifying performance bottlenecks.",
    )
    parser.add_argument(
        "--pytest",
        action="store_true",
        help="Run tests using pytest with snapshot testing instead of custom test runner. "
        "Supports -k for filtering, --update-snapshots for updating expected results.",
    )
    parser.add_argument(
        "--update-snapshots",
        action="store_true",
        help="Update pytest snapshots with current analysis results (use with --pytest). "
        "Equivalent to: pytest --snapshot-update",
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=str,
        help="Optional path to contract file or project directory (alternative to --contract)",
    )

    args = parser.parse_args()

    if args.pytest:
        # Run tests using pytest with snapshot testing
        import subprocess

        cmd = ["pytest", "slither/analyses/data_flow/tests/", "-v"]
        if args.update_snapshots:
            cmd.append("--snapshot-update")
        if args.path:
            # Allow filtering by contract name, e.g., --pytest Assert.sol
            cmd.extend(["-k", args.path])
        return subprocess.call(cmd)

    if args.generate_expected:
        # Generate expected results from current analysis
        from slither.analyses.data_flow.test import generate_expected_results

        contracts_dir = Path(args.contracts_dir or "../contracts/src")
        if not contracts_dir.exists():
            console.print(f"[red]Contracts directory not found: {contracts_dir}[/red]")
            return 1

        # If a path is provided, treat it as a contract file name
        contract_file = None
        if args.path:
            contract_file = args.path
            # Remove directory path if provided, keep only filename
            if "/" in contract_file or "\\" in contract_file:
                contract_file = Path(contract_file).name
            # Ensure it ends with .sol
            if not contract_file.endswith(".sol"):
                contract_file = f"{contract_file}.sol"

        generate_expected_results(contracts_dir, contract_file=contract_file)
        return 0
    elif args.show:
        # Show verbose output for a specific test
        from slither.analyses.data_flow.verbose import show_test_output

        contracts_dir = args.contracts_dir or "../contracts/src"
        show_test_output(args.show, function_name=args.function, contracts_dir=contracts_dir)
        return 0
    elif args.test:
        # Automated test mode
        from slither.analyses.data_flow.test import run_tests

        contracts_dir = Path(args.contracts_dir or "../contracts/src")
        if not contracts_dir.exists():
            console.print(f"[red]Contracts directory not found: {contracts_dir}[/red]")
            return 1
        return run_tests(contracts_dir, verbose=args.verbose)
    else:
        # Verbose mode (original behavior)
        from slither.analyses.data_flow.verbose import run_verbose

        # Priority: positional argument > --contract > --contracts-dir > default
        if args.path:
            contract_path = args.path
        elif args.contract:
            contract_path = args.contract
        elif args.contracts_dir:
            # Use contracts_dir if explicitly provided
            contract_path = args.contracts_dir
        else:
            # Fallback to default (for backward compatibility)
            contract_path = "../contracts/src/FunctionArgs.sol"

        # Convert to absolute path for better handling, but Slither can handle both
        contract_path_obj = Path(contract_path)
        if contract_path_obj.exists():
            # Use absolute path if it exists
            contract_path = str(contract_path_obj.resolve())
        else:
            # Even if path doesn't exist as-is, let Slither try (it handles project detection)
            # Just warn the user
            console.print(f"[yellow]Warning: Path may not exist: {contract_path}[/yellow]")
            console.print(
                "[dim]Slither will attempt to detect project type (Foundry/Hardhat/etc.)[/dim]"
            )

        run_verbose(
            contract_path,
            debug=args.debug,
            function_name=args.function,
            contract_name=args.contract_name,
            embed=args.embed,
            skip_compile=args.skip_compile,
            timeout_ms=args.timeout,
            skip_range_solving=args.skip_range_solving,
            show_telemetry=args.telemetry,
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
