#!/usr/bin/env python3
"""
Simple batch runner for interval analysis testing.
"""

import subprocess
import sys
from pathlib import Path

# Path to testing.py script
TESTING_SCRIPT = "testing.py"

# List of Solidity files to test
FILES = [
    "tests/e2e/detectors/test_data/interval/0.8.10/ConstraintApplicationTest.sol",
    "tests/e2e/detectors/test_data/interval/0.8.10/ComprehensiveMultiplicationTests.sol",
    "tests/e2e/detectors/test_data/interval/0.8.10/ComprehensiveDivisionTests.sol",
]


def run_test(file_path: str) -> bool:
    """Run testing.py on a file and return True if it passes"""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "slither/analyses/data_flow/interval_enhanced/tests/testing.py",
                file_path,
            ],
            capture_output=True,
            timeout=120,
        )
        return result.returncode == 0
    except:
        return False


def main():
    passed = []
    failed = []

    for file_path in FILES:
        if not Path(file_path).exists():
            failed.append(file_path)
            continue

        if run_test(file_path):
            passed.append(file_path)
        else:
            failed.append(file_path)

    print(f"Tested {len(FILES)} files - Passed: {len(passed)}, Failed: {len(failed)}")

    if passed:
        print(f"\nPASSED:")
        for f in passed:
            print(f"  {Path(f).name}")

    if failed:
        print(f"\nFAILED:")
        for f in failed:
            print(f"  {Path(f).name}")


if __name__ == "__main__":
    main()
