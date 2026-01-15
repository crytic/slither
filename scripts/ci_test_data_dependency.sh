#!/usr/bin/env bash
set -euo pipefail

### Test data dependency

if ! python ./examples/scripts/data_dependency.py ./examples/scripts/data_dependency.sol; then
    echo "data dependency failed"
    exit 1
fi
exit 0
