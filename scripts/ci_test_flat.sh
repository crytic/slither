#!/usr/bin/env bash

### Test slither-prop

cd examples/flat || exit 1

if ! slither-flat b.sol; then
    echo "slither-flat failed"
    exit 1
fi

exit 0
