#!/usr/bin/env bash

# Source common CI test setup
source "$(dirname "$0")/ci_test_common.sh"

### Test

if ! slither "tests/*.json" --config "tests/config/slither.config.json"; then
    echo "Config failed"
    exit 1
fi
