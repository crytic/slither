#!/usr/bin/env bash
set -euo pipefail

### Test

solc-select use 0.7.0

if ! slither --config-file "tests/e2e/config/test_json_config/slither.config.json" detect "tests/e2e/config/test_json_config/test.sol"; then
    echo "Config failed"
    exit 1
fi
