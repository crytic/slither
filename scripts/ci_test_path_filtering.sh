#!/usr/bin/env bash
set -euo pipefail

### Test path filtering across POSIX and Windows

solc-select use 0.8.0
slither --config "tests/e2e/config/test_path_filtering/slither.config.json" detect "tests/e2e/config/test_path_filtering/test_path_filtering.sol" > "output.txt" 2>&1

if ! grep -q "0 result(s) found" "output.txt"
then
  echo "Path filtering across POSIX and Windows failed"
  rm output.txt
  exit 5
else
  rm output.txt
fi
