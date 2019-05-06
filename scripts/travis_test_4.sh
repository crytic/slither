#!/usr/bin/env bash

### Test Detectors

DIR="$(cd "$(dirname "$0")" && pwd)"

CURRENT_PATH=$(pwd)
TRAVIS_PATH='/home/travis/build/crytic/slither'
# test_slither file.sol detectors
test_slither(){

    expected="$DIR/../tests/expected_json/$(basename $1 .sol).$2.json"

    # run slither detector on input file and save output as json
    slither "$1" --solc-disable-warnings --detect "$2" --json "$DIR/tmp-test.json" --solc solc-0.4.25
    if [ $? -eq 255 ]
    then
        echo "Slither crashed"
        exit -1
    fi

    if [ ! -f "$DIR/tmp-test.json" ]; then
        echo ""
        echo "Missing generated file"
        echo ""
        exit 1
    fi

    sed "s|$CURRENT_PATH|$TRAVIS_PATH|g" "$DIR/tmp-test.json" -i
    result=$(python "$DIR/json_diff.py" "$expected" "$DIR/tmp-test.json")

    rm "$DIR/tmp-test.json"
    if [ "$result" != "{}" ]; then
      echo ""
      echo "failed test of file: $1, detector: $2"
      echo ""
      echo "$result"
      echo ""
      exit 1
    fi

    # run slither detector on input file and save output as json
    slither "$1" --solc-disable-warnings --detect "$2" --legacy-ast --json "$DIR/tmp-test.json" --solc solc-0.4.25
    if [ $? -eq 255 ]
    then
        echo "Slither crashed"
        exit -1
    fi

    if [ ! -f "$DIR/tmp-test.json" ]; then
        echo ""
        echo "Missing generated file"
        echo ""
        exit 1
    fi

    sed "s|$CURRENT_PATH|$TRAVIS_PATH|g" "$DIR/tmp-test.json" -i
    result=$(python "$DIR/json_diff.py" "$expected" "$DIR/tmp-test.json")
	
    rm "$DIR/tmp-test.json"
    if [ "$result" != "{}" ]; then
      echo ""
      echo "failed test of file: $1, detector: $2"
      echo ""
      echo "$result"
      echo ""
      exit 1
    fi
}


test_slither tests/deprecated_calls.sol "deprecated-standards"
test_slither tests/erc20_indexed.sol "erc20-indexed"
test_slither tests/incorrect_erc20_interface.sol "erc20-interface"
test_slither tests/uninitialized.sol "uninitialized-state"
test_slither tests/backdoor.sol "backdoor"
test_slither tests/backdoor.sol "suicidal"
test_slither tests/pragma.0.4.24.sol "pragma"
test_slither tests/old_solc.sol.json "solc-version"
test_slither tests/reentrancy.sol "reentrancy-eth"
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
test_slither tests/external_function_2.sol "external-function"
test_slither tests/naming_convention.sol "naming-convention"
#test_slither tests/complex_func.sol "complex-function"
test_slither tests/controlled_delegatecall.sol "controlled-delegatecall"
test_slither tests/constant.sol "constant-function"
test_slither tests/unused_return.sol "unused-return"
test_slither tests/shadowing_abstract.sol "shadowing-abstract"
test_slither tests/shadowing_state_variable.sol "shadowing-state"
test_slither tests/timestamp.sol "timestamp"
test_slither tests/multiple_calls_in_loop.sol "calls-loop"
test_slither tests/shadowing_builtin_symbols.sol "shadowing-builtin"
test_slither tests/shadowing_local_variable.sol "shadowing-local"
test_slither tests/solc_version_incorrect.sol "solc-version"
test_slither tests/right_to_left_override.sol "rtlo"
