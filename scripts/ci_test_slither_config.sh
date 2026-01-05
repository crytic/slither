#!/usr/bin/env bash

# Source common CI test setup
source "$(dirname "$0")/ci_test_common.sh"

### Test

solc-select use 0.7.0

if ! slither "tests/e2e/config/test_json_config/test.sol" --config "tests/e2e/config/test_json_config/slither.config.json"; then
    echo "Config failed"
    exit 1
fi
