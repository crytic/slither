#!/usr/bin/env bash

### Test Detectors

DIR="$(cd "$(dirname "$0")" && pwd)"

# test_slither file.sol detectors
test_slither(){
    expected="$DIR/../tests/expected_json/$(basename $1 .sol).$2.json"
    actual="$DIR/$(basename $1 .sol).$2.json"

    # run slither detector on input file and save output as json
    slither "$1" --disable-solc-warnings --detectors "$2" --json "$DIR/tmp-test.json"

    # convert json file to pretty print and write to destination folder
    python "$DIR/pretty_print_and_sort_json.py" "$DIR/tmp-test.json" "$actual"

    # remove the raw un-prettified json file
    rm "$DIR/tmp-test.json"

    result=$(diff "$expected" "$actual")

    if [ "$result" != "" ]; then
      rm "$actual"
      echo ""
      echo "failed test of file: $1, detector: $2"
      echo ""
      echo "$result"
      echo ""
      exit 1
    else
      rm "$actual"
    fi

    # run slither detector on input file and save output as json
    slither "$1" --disable-solc-warnings --detectors "$2" --compact-ast --json "$DIR/tmp-test.json"

    # convert json file to pretty print and write to destination folder
    python "$DIR/pretty_print_and_sort_json.py" "$DIR/tmp-test.json" "$actual"

    # remove the raw un-prettified json file
    rm "$DIR/tmp-test.json"

    result=$(diff "$expected" "$actual")

    if [ "$result" != "" ]; then
      rm "$actual"
      echo ""
      echo "failed test of file: $1, detector: $2"
      echo ""
      echo "$result"
      echo ""
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
#test_slither tests/complex_func.sol "complex-function"

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
