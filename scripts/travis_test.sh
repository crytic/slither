#!/usr/bin/env bash

### Test Detectors

# test_slither file.sol --detect-detectors number_results
test_slither(){
    slither "$1" --disable-solc-warnings "$2"
    if [ $? -ne "$3" ]; then
        exit 1
    fi

    slither "$1" --disable-solc-warnings "$2" --compact-ast
    if [ $? -ne "$3" ]; then
        exit 1
    fi
}

test_slither tests/uninitialized.sol "--detect-uninitialized-state" 3
test_slither tests/backdoor.sol "--detect-backdoor" 1
test_slither tests/backdoor.sol "--detect-suicidal" 1
test_slither tests/pragma.0.4.24.sol "--detect-pragma" 1
test_slither tests/old_solc.sol.json "--detect-solc-version" 1
test_slither tests/reentrancy.sol "--detect-reentrancy" 1
test_slither tests/uninitialized_storage_pointer.sol "--detect-uninitialized-storage" 1
test_slither tests/tx_origin.sol "--detect-tx-origin" 2
test_slither tests/unused_state.sol "--detect-unused-state" 1
test_slither tests/locked_ether.sol "--detect-locked-ether" 1
test_slither tests/arbitrary_send.sol "--detect-arbitrary-send" 2
test_slither tests/inline_assembly_contract.sol "--detect-assembly" 1
test_slither tests/inline_assembly_library.sol "--detect-assembly" 2
test_slither tests/naming_convention.sol "--detect-naming-convention" 10
test_slither tests/low_level_calls.sol "--detect-low-level-calls" 1
test_slither tests/const_state_variables.sol "--detect-const-candidates-state" 2

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
