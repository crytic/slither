#!/usr/bin/env bash

### Test

solc-select use 0.7.0

if slither "tests/config/test.sol" --solc-ast; then
    echo "--solc-ast failed"
    exit 1
fi

if slither "tests/config/test.sol" --solc-disable-warnings; then
    echo "--solc-disable-warnings failed"
    exit 1
fi

if slither "tests/config/test.sol" --disable-color; then
    echo "--disable-color failed"
    exit 1
fi
