#!/usr/bin/env bash

### Test Detectors

slither tests/uninitialized.sol --disable-solc-warnings
if [ $? -ne 2 ]; then
    exit 1
fi

# contains also the test for the suicidal detector
slither tests/backdoor.sol --disable-solc-warnings
if [ $? -ne 2 ]; then
    exit 1
fi

slither tests/pragma.0.4.24.sol --disable-solc-warnings
if [ $? -ne 1 ]; then
    exit 1
fi

slither tests/old_solc.sol.json --solc-ast
if [ $? -ne 1 ]; then
    exit 1
fi

slither tests/reentrancy.sol --disable-solc-warnings
if [ $? -ne 1 ]; then
    exit 1
fi

slither tests/uninitialized_storage_pointer.sol --disable-solc-warnings
if [ $? -ne 1 ]; then
    exit 1
fi

slither tests/tx_origin.sol --disable-solc-warnings
if [ $? -ne 2 ]; then
    exit 1
fi

slither tests/unused_state.sol
if [ $? -ne 3 ]; then
    exit 1
fi

slither tests/locked_ether.sol
if [ $? -ne 3 ]; then
    exit 1
fi

slither tests/arbitrary_send.sol --disable-solc-warnings
if [ $? -ne 2 ]; then
    exit 1
fi

slither tests/inline_assembly_contract.sol --disable-solc-warnings
if [ $? -ne 2 ]; then
    exit 1
fi

slither tests/inline_assembly_library.sol --disable-solc-warnings
if [ $? -ne 3 ]; then
    exit 1
fi

slither tests/const_state_variables.sol --detect-const-candidates-state
if [ $? -ne 2 ]; then
    exit 1
fi

### Test scripts

python examples/scripts/functions_called.py examples/scripts/functions_called.sol
if [ $? -ne 0 ]; then
    exit 1
fi

python examples/scripts/functions_writing.py examples/scripts/functions_writing.sol
if [ $? -ne 0 ]; then
    exit 1
fi

python examples/scripts/variable_in_condition.py examples/scripts/variable_in_condition.sol
if [ $? -ne 0 ]; then
    exit 1
fi
exit 0
