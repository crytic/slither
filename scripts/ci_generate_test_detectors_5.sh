#!/usr/bin/env bash

source "$(dirname "$0")""/ci_test.sh"

solc use "0.5.1"

# Be sure that only one of the following line is uncommented before running the script

# generate_expected_json tests/void-cst.sol "void-cst"
# generate_expected_json tests/solc_version_incorrect_05.ast.json "solc-version"
# generate_expected_json tests/uninitialized-0.5.1.sol "uninitialized-state"
# generate_expected_json tests/backdoor.sol "backdoor"
# generate_expected_json tests/backdoor.sol "suicidal"
# generate_expected_json tests/old_solc.sol.json "solc-version"
# generate_expected_json tests/reentrancy-0.5.1.sol "reentrancy-eth"
# generate_expected_json tests/reentrancy-0.5.1-events.sol "reentrancy-events"
# generate_expected_json tests/tx_origin-0.5.1.sol "tx-origin"
# generate_expected_json tests/locked_ether-0.5.1.sol "locked-ether"
# generate_expected_json tests/arbitrary_send-0.5.1.sol "arbitrary-send"
# generate_expected_json tests/inline_assembly_contract-0.5.1.sol "assembly"
# generate_expected_json tests/inline_assembly_library-0.5.1.sol "assembly"
# generate_expected_json tests/constant-0.5.1.sol "constant-function-asm"
# generate_expected_json tests/constant-0.5.1.sol "constant-function-state"
# generate_expected_json tests/incorrect_equality.sol "incorrect-equality"
# generate_expected_json tests/too_many_digits.sol "too-many-digits"
# generate_expected_json tests/unchecked_lowlevel-0.5.1.sol "unchecked-lowlevel"
# generate_expected_json tests/unchecked_send-0.5.1.sol "unchecked-send"

