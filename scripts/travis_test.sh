#!/usr/bin/env bash

./slither.py examples/bugs/uninitialized.sol --disable-solc-warnings
if [ $? -ne 1 ]; then
    exit 1
fi

./slither.py examples/bugs/backdoor.sol --disable-solc-warnings
if [ $? -ne 1 ]; then
    exit 1
fi

exit 0
