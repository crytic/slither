#!/usr/bin/env bash

### Test Detectors

# test_slither file.sol detectors
test_slither(){
    expected="tests/$(basename $1 .sol).$2.json"
    actual="$(basename $1 .sol).$2.json"

    slither "$1" --disable-solc-warnings --detectors "$2" --json tmp.json

    cat tmp.json | python -m json.tool > "$actual"
    rm tmp.json

    result=$(diff "$expected" "$actual")

    if [ "$result" != "" ]; then
      rm "$actual"
      echo "\nfailed test of file: $1, detector: $2\n"
      echo "$result\n"
      exit 1
    else
      rm "$actual"
    fi

    slither "$1" --disable-solc-warnings --detectors "$2" --compact-ast --json tmp.json

    cat tmp.json | python -m json.tool > "$actual"
    rm tmp.json

    result=$(diff "$expected" "$actual")

    if [ "$result" != "" ]; then
      rm "$actual"
      echo "\nfailed test of file: $1, detector: $2\n"
      echo "$result\n"
      exit 1
    else
      rm "$actual"
    fi
}

test_slither tests/uninitialized.sol "uninitialized-state"
test_slither tests/backdoor.sol "backdoor"
test_slither tests/backdoor.sol "suicidal"
test_slither tests/pragma.0.4.24.sol "pragma"
test_slither tests/old_solc.sol.json "solc-version"
test_slither tests/reentrancy.sol "reentrancy"
test_slither tests/uninitialized_storage_pointer.sol "uninitialized-storage"
test_slither tests/tx_origin.sol "tx-origin"
test_slither tests/unused_state.sol "unused-state"
test_slither tests/locked_ether.sol "locked-ether"
test_slither tests/arbitrary_send.sol "arbitrary-send"
test_slither tests/inline_assembly_contract.sol "assembly"
test_slither tests/inline_assembly_library.sol "assembly"
test_slither tests/low_level_calls.sol "low-level-calls"
test_slither tests/const_state_variables.sol "constable-states"
test_slither tests/external_function.sol "external-function"
test_slither tests/naming_convention.sol "naming-convention"

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
