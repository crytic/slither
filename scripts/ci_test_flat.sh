#!/usr/bin/env bash

### Test slither-prop

cd examples/flat || exit 1
slither-flat b.sol

if [ $? -eq 0 ]
then
    exit 0
fi

echo "slither-flat failed"
exit -1
