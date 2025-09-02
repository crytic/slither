#!/usr/bin/env bash

# Source common CI test setup
source "$(dirname "$0")/ci_test_common.sh"

### Test data dependency

if ! python ./examples/scripts/data_dependency.py ./examples/scripts/data_dependency.sol; then
    echo "data dependency failed"
    exit 1
fi
exit 0
