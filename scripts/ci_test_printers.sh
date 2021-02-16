#!/usr/bin/env bash

### Test printer 

# Needed for evm printer
pip install evm-cfg-builder

if ! slither "tests/*.json" --print all --json -; then
    echo "Printer tests failed"
    exit 1
fi

solc-select use "0.5.1"

slither examples/scripts/test_evm_api.sol --print evm 
