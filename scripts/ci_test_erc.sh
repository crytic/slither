#!/usr/bin/env bash
set -euo pipefail

# Source common CI test setup
source "$(dirname "$0")/ci_test_common.sh"

### Test slither-check-erc

DIR_TESTS="tests/tools/check_erc"

solc-select use 0.5.1
slither-check-erc "$DIR_TESTS/erc20.sol" ERC20 2>&1 | tee test_1.txt
DIFF=$(diff test_1.txt "$DIR_TESTS/test_1.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-erc 1 failed"
    cat test_1.txt
    echo ""
    cat "$DIR_TESTS/test_1.txt"
    exit 255
fi


rm test_1.txt
