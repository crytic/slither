#!/usr/bin/env bash
set -euo pipefail

# Source common CI test setup
source "$(dirname "$0")/ci_test_common.sh"

### Test slither-prop

cd examples/slither-prop || exit 1
slither-prop . --contract ERC20Buggy
if [ ! -f contracts/crytic/TestERC20BuggyTransferable.sol ]; then
    echo "slither-prop failed"
    return 1
fi
