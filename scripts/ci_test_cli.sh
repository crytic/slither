#!/usr/bin/env bash

### Test

solc-select use 0.7.0

if ! slither "tests/e2e/config/test_json_config/test.sol" --solc-ast --no-fail-pedantic; then
    echo "--solc-ast failed"
    exit 1
fi

if ! slither "tests/e2e/config/test_json_config/test.sol" --solc-disable-warnings --no-fail-pedantic; then
    echo "--solc-disable-warnings failed"
    exit 1
fi

if ! slither "tests/e2e/config/test_json_config/test.sol" --disable-color --no-fail-pedantic; then
    echo "--disable-color failed"
    exit 1
fi
