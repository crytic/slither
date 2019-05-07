#!/usr/bin/env bash

### Test 

slither "tests/*.json" --solc-ast --ignore-return-value

if [ $? -ne 0 ]; then
    echo "--solc-ast failed"
    exit 1
fi

slither "tests/*0.5*.sol" --solc-disable-warnings --ignore-return-value

if [ $? -ne 0 ]; then
    echo "--solc-disable-warnings failed"
    exit 1
fi

slither "tests/*0.5*.sol" --disable-color --ignore-return-value

if [ $? -ne 0 ]; then
    echo "--disable-color failed"
    exit 1
fi
