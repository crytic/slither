#!/usr/bin/env bash

### Test Detectors

# test_slither file.sol detectors number_results
test_slither(){
    slither "$1" --disable-solc-warnings --detectors "$2"
    if [ $? -ne "$3" ]; then
        exit 1
    fi

    slither "$1" --disable-solc-warnings --detectors "$2" --compact-ast
    if [ $? -ne "$3" ]; then
        exit 1
    fi
}

test_slither tests/uninitialized.sol "uninitialized-state" 4
test_slither tests/backdoor.sol "backdoor" 1
test_slither tests/backdoor.sol "suicidal" 1
test_slither tests/pragma.0.4.24.sol "pragma" 1
test_slither tests/old_solc.sol.json "solc-version" 1
test_slither tests/reentrancy.sol "reentrancy" 1
test_slither tests/uninitialized_storage_pointer.sol "uninitialized-storage" 1
test_slither tests/tx_origin.sol "tx-origin" 2
test_slither tests/unused_state.sol "unused-state" 1
test_slither tests/locked_ether.sol "locked-ether" 1
test_slither tests/arbitrary_send.sol "arbitrary-send" 2
test_slither tests/complex_func.sol "complex-function" 3
test_slither tests/inline_assembly_contract.sol "assembly" 1
test_slither tests/inline_assembly_library.sol "assembly" 2
test_slither tests/naming_convention.sol "naming-convention" 10
test_slither tests/low_level_calls.sol "low-level-calls" 1
test_slither tests/const_state_variables.sol "const-candidates-state" 2
test_slither tests/external_function.sol "external-function" 4

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
