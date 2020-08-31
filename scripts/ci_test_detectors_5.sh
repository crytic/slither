#!/usr/bin/env bash

source "$(dirname "$0")""/ci_test.sh"
  
solc use "0.5.1"

test_slither tests/void-cst.sol "void-cst"
test_slither tests/solc_version_incorrect_05.ast.json "solc-version"
test_slither tests/unchecked_lowlevel-0.5.1.sol "unchecked-lowlevel"
test_slither tests/unchecked_send-0.5.1.sol "unchecked-send"
test_slither tests/uninitialized-0.5.1.sol "uninitialized-state"
test_slither tests/backdoor.sol "backdoor"
test_slither tests/backdoor.sol "suicidal"
test_slither tests/old_solc.sol.json "solc-version"
test_slither tests/reentrancy-0.5.1.sol "reentrancy-eth"
test_slither tests/reentrancy-0.5.1-events.sol "reentrancy-events"
test_slither tests/tx_origin-0.5.1.sol "tx-origin"
test_slither tests/unused_state.sol "unused-state"
test_slither tests/locked_ether-0.5.1.sol "locked-ether"
test_slither tests/arbitrary_send-0.5.1.sol "arbitrary-send"
test_slither tests/inline_assembly_contract-0.5.1.sol "assembly"
test_slither tests/inline_assembly_library-0.5.1.sol "assembly"
test_slither tests/low_level_calls.sol "low-level-calls"
test_slither tests/const_state_variables.sol "constable-states"
test_slither tests/external_function.sol "external-function"
test_slither tests/external_function_2.sol "external-function"
test_slither tests/naming_convention.sol "naming-convention"
#test_slither tests/complex_func.sol "complex-function"
test_slither tests/controlled_delegatecall.sol "controlled-delegatecall"
test_slither tests/constant-0.5.1.sol "constant-function-asm"
test_slither tests/constant-0.5.1.sol "constant-function-state"
test_slither tests/unused_return.sol "unused-return"
test_slither tests/timestamp.sol "timestamp"
test_slither tests/incorrect_equality.sol "incorrect-equality"
test_slither tests/too_many_digits.sol "too-many-digits"


### Test scripts

if ! python examples/scripts/functions_called.py examples/scripts/functions_called.sol; then
    exit 1
fi

if ! python examples/scripts/functions_writing.py examples/scripts/functions_writing.sol; then
    exit 1
fi

if ! python examples/scripts/variable_in_condition.py examples/scripts/variable_in_condition.sol; then
    exit 1
fi
exit 0
