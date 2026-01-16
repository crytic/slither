#!/usr/bin/env bash
set -euo pipefail

### Test slither analysis on a contract

DIR_TESTS="tests/tools/etherscan"

solc-select use 0.4.25 --always-install

echo "::group::BalanceChecker analysis"
if ! slither "$DIR_TESTS/BalanceChecker.sol" --no-fail-pedantic; then
    echo "BalanceChecker test failed"
    exit 1
fi
echo "::endgroup::"

exit 0
