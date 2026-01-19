#!/usr/bin/env python3
"""
Benchmark Slither performance against real-world smart contract projects.

Usage:
    # First time: clone all projects and install dependencies
    python scripts/benchmark_perf.py --setup

    # Run benchmark on current checkout (no branch comparison)
    python scripts/benchmark_perf.py --no-branch-compare

    # Run on specific projects only
    python scripts/benchmark_perf.py --projects v4-core,comet --no-branch-compare

    # Compare across branches (default behavior)
    python scripts/benchmark_perf.py

    # Output JSON for CI/automation
    python scripts/benchmark_perf.py --no-branch-compare --json

    # Benchmark from a worktree (for parallel benchmarking)
    python scripts/benchmark_perf.py --slither-path /path/to/worktree --json

    # Compare against baseline and post to PR
    python scripts/benchmark_perf.py --slither-path /path/to/worktree \\
        --baseline /tmp/baseline.json --pr 123
"""

import argparse
import fcntl
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

BENCH_DIR = Path("/tmp/slither-bench")
LOCK_FILE = Path("/tmp/slither-bench.lock")

FOUNDRY_BIN = Path.home() / ".foundry" / "bin"
if FOUNDRY_BIN.exists():
    os.environ["PATH"] = f"{FOUNDRY_BIN}:{os.environ.get('PATH', '')}"

# Project configurations
PROJECTS = {
    "v4-core": {
        "url": "https://github.com/Uniswap/v4-core",
        "setup": ["forge install"],
    },
    "comet": {
        "url": "https://github.com/compound-finance/comet",
        "setup": ["yarn install"],
    },
    "aave-v3-core": {
        "url": "https://github.com/aave/aave-v3-core",
        "setup": ["npm install"],
    },
    "lido-dao": {
        "url": "https://github.com/lidofinance/lido-dao",
        "setup": ["yarn install"],
    },
    "optimism": {
        "url": "https://github.com/ethereum-optimism/optimism",
        "setup": ["pnpm install"],
        "subdir": "packages/contracts-bedrock",
    },
}

# Branches to compare (used when --no-branch-compare is not set)
BRANCHES = [
    "master",
    "perf/transitive-closure-worklist",
]

ITERATIONS = 1


@contextmanager
def benchmark_lock(wait: bool = True):
    """Acquire exclusive lock for benchmarking.

    Args:
        wait: If True, block until lock available. If False, raise if locked.
    """
    lock_file = LOCK_FILE.open("w")
    try:
        flags = fcntl.LOCK_EX if wait else (fcntl.LOCK_EX | fcntl.LOCK_NB)
        if wait:
            print("Waiting for benchmark lock...", file=sys.stderr)
        fcntl.flock(lock_file, flags)
        if wait:
            print("Lock acquired, starting benchmark", file=sys.stderr)
        yield
    except BlockingIOError:
        lock_file.close()
        raise SystemExit("Another benchmark is running. Use --wait to queue.")
    finally:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()


def setup_projects(project_names: list[str]) -> None:
    """Clone repos and install dependencies for specified projects."""
    BENCH_DIR.mkdir(parents=True, exist_ok=True)

    for name in project_names:
        config = PROJECTS[name]
        project_dir = BENCH_DIR / name

        # Clone if not exists
        if not project_dir.exists():
            print(f"Cloning {name}...")
            subprocess.run(
                ["git", "clone", "--depth", "1", config["url"], str(project_dir)],
                check=True,
            )
        else:
            print(f"{name} already exists, skipping clone")

        # Run setup commands
        work_dir = project_dir / config.get("subdir", "")
        for cmd in config.get("setup", []):
            print(f"Running '{cmd}' in {name}...")
            subprocess.run(cmd, shell=True, cwd=work_dir, check=True)


def run_slither(project_path: str, slither_cwd: Path | None = None) -> float:
    """Run slither and return elapsed time.

    Args:
        project_path: Path to the project to analyze.
        slither_cwd: Directory to run slither from (for worktree support).
    """
    start = time.perf_counter()
    subprocess.run(
        ["uv", "run", "slither", project_path],
        capture_output=True,
        cwd=slither_cwd,
    )
    return time.perf_counter() - start


def get_project_path(name: str) -> str:
    """Get the path to analyze for a project."""
    config = PROJECTS[name]
    base = BENCH_DIR / name
    if "subdir" in config:
        return str(base / config["subdir"])
    return str(base)


def benchmark_current(
    project_names: list[str],
    quiet: bool = False,
    slither_cwd: Path | None = None,
) -> dict[str, float]:
    """Benchmark current checkout against specified projects.

    Args:
        project_names: List of project names to benchmark.
        quiet: Suppress output if True.
        slither_cwd: Directory to run slither from (for worktree support).
    """
    results = {}
    for name in project_names:
        path = get_project_path(name)
        if not Path(path).exists():
            if not quiet:
                print(f"  {name}: SKIPPED (not found, run --setup first)")
            continue

        times = [run_slither(path, slither_cwd) for _ in range(ITERATIONS)]
        avg = sum(times) / len(times)
        results[name] = round(avg, 1)
        if not quiet:
            print(f"  {name}: {avg:.1f}s")

    return results


def benchmark_branches(project_names: list[str], branches: list[str], quiet: bool = False) -> dict:
    """Benchmark multiple branches against specified projects."""
    results = {}

    for branch in branches:
        if not quiet:
            print(f"\n=== {branch} ===")
        subprocess.run(["git", "checkout", branch], capture_output=True)
        subprocess.run(["git", "pull", "--ff-only"], capture_output=True)

        results[branch] = benchmark_current(project_names, quiet=quiet)

    subprocess.run(["git", "checkout", "master"], capture_output=True)
    return results


def format_results_markdown(
    results: dict[str, float], baseline: dict[str, float] | None = None
) -> str:
    """Format benchmark results as markdown table.

    Args:
        results: Benchmark results {project_name: time_seconds}.
        baseline: Optional baseline results for comparison.

    Returns:
        Markdown-formatted table string.
    """
    lines = [
        "## Benchmark Results",
        "",
        "| Project | Time | vs Baseline |",
        "|---------|------|-------------|",
    ]
    for proj, time_s in results.items():
        if baseline and proj in baseline:
            base_time = baseline[proj]
            delta = ((base_time - time_s) / base_time) * 100 if base_time else 0
            lines.append(f"| {proj} | {time_s}s | {delta:+.1f}% |")
        else:
            lines.append(f"| {proj} | {time_s}s | - |")
    return "\n".join(lines)


def load_baseline(baseline_path: Path) -> dict[str, float]:
    """Load baseline results from JSON file.

    Args:
        baseline_path: Path to baseline JSON file.

    Returns:
        Baseline results dictionary.
    """
    with baseline_path.open() as f:
        return json.load(f)


def print_pr_comment_command(
    pr_number: int, results: dict[str, float], baseline: dict[str, float] | None = None
) -> None:
    """Print the gh command to post results as PR comment (no auto-posting).

    Args:
        pr_number: GitHub PR number.
        results: Benchmark results {project_name: time_seconds}.
        baseline: Optional baseline results for comparison.
    """
    body = format_results_markdown(results, baseline)
    # Print markdown preview
    print("=== PR Comment Preview ===")
    print(body)
    print()
    # Print command user can run
    escaped_body = body.replace("'", "'\\''")  # Escape single quotes for shell
    print("=== Command to post ===")
    print(f"gh pr comment {pr_number} --body $'{escaped_body}'")


def print_comparison(results: dict) -> None:
    """Print comparison table with percentage changes from baseline."""
    print("\n=== RESULTS ===")
    baseline = results.get("master", {})

    for branch, data in results.items():
        if branch == "master":
            print(f"{branch}: {data}")
        else:
            changes = {}
            for proj, t in data.items():
                base = baseline.get(proj, t)
                pct = ((base - t) / base) * 100 if base else 0
                changes[proj] = f"{t}s ({pct:+.1f}%)"
            print(f"{branch}: {changes}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Slither performance against smart contract projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Clone repos and install dependencies",
    )
    parser.add_argument(
        "--projects",
        type=str,
        help=f"Comma-separated list of projects to benchmark (default: all). "
        f"Available: {', '.join(PROJECTS.keys())}",
    )
    parser.add_argument(
        "--no-branch-compare",
        action="store_true",
        help="Just time the current checkout without switching branches",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON only (no human-readable output)",
    )
    parser.add_argument(
        "--branches",
        type=str,
        help=f"Comma-separated list of branches to compare (default: {', '.join(BRANCHES)})",
    )
    parser.add_argument(
        "--slither-path",
        type=str,
        help="Path to slither installation (worktree) to benchmark from",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        help="Path to baseline JSON file for comparison",
    )
    parser.add_argument(
        "--pr",
        type=int,
        help="GitHub PR number to post results as a comment",
    )
    parser.add_argument(
        "--no-lock",
        action="store_true",
        help="Skip lock acquisition (for isolated environments)",
    )

    args = parser.parse_args()

    # Determine which projects to use
    if args.projects:
        project_names = [p.strip() for p in args.projects.split(",")]
        invalid = [p for p in project_names if p not in PROJECTS]
        if invalid:
            print(f"Unknown projects: {invalid}", file=sys.stderr)
            print(f"Available: {list(PROJECTS.keys())}", file=sys.stderr)
            sys.exit(1)
    else:
        project_names = list(PROJECTS.keys())

    # Handle setup mode
    if args.setup:
        setup_projects(project_names)
        print("\nSetup complete. Run without --setup to benchmark.")
        return

    # Only chdir if not using --slither-path (worktree mode)
    slither_cwd = None
    if args.slither_path:
        slither_cwd = Path(args.slither_path)
        if not slither_cwd.exists():
            print(f"Error: --slither-path does not exist: {slither_cwd}", file=sys.stderr)
            sys.exit(1)
    else:
        os.chdir(Path(__file__).parent.parent)

    # Load baseline if provided
    baseline = None
    if args.baseline:
        baseline_path = Path(args.baseline)
        if not baseline_path.exists():
            print(f"Error: --baseline file does not exist: {baseline_path}", file=sys.stderr)
            sys.exit(1)
        baseline = load_baseline(baseline_path)

    # Determine branches
    branches = BRANCHES
    if args.branches:
        branches = [b.strip() for b in args.branches.split(",")]

    # Run benchmark (with lock unless --no-lock)
    def run_benchmark():
        if args.no_branch_compare or args.slither_path:
            if not args.json:
                print("=== Benchmark Results ===")
            return benchmark_current(project_names, quiet=args.json, slither_cwd=slither_cwd)
        return benchmark_branches(project_names, branches, quiet=args.json)

    if args.no_lock:
        results = run_benchmark()
    else:
        with benchmark_lock():
            results = run_benchmark()

    # Print PR comment command if requested (no auto-posting)
    if args.pr:
        print_pr_comment_command(args.pr, results, baseline)
        return  # Don't print JSON when using --pr (output already includes preview)

    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    elif not args.no_branch_compare and not args.slither_path:
        print_comparison(results)
        print("\n" + json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
