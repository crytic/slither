#!/usr/bin/env bash

slither examples/bugs/uninitialized.sol --disable-solc-warnings
if [ $? -ne 1 ]; then
    exit 1
fi

slither examples/bugs/backdoor.sol --disable-solc-warnings
if [ $? -ne 1 ]; then
    exit 1
fi

exit 0
