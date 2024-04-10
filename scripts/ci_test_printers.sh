#!/usr/bin/env bash

### Test the EVM printer

pip install evm-cfg-builder
solc-select use "0.5.1"
if ! slither examples/scripts/test_evm_api.sol --print evm; then
  echo "EVM printer failed"
fi