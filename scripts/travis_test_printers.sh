#!/usr/bin/env bash

### Test printer 

# Needed for evm printer
pip install evm-cfg-builder

slither "tests/*.json" --print all

if [ $? -ne 0 ]; then
    echo "Printer tests failed"
    exit 1
fi

