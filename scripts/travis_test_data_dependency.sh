#!/usr/bin/env bash

### Test data dependecy

python ./examples/scripts/data_dependency.py ./examples/scripts/data_dependency.sol

if [ $? -ne 0 ]; then
    echo "data dependency failed"
    exit 1
fi
exit 0
