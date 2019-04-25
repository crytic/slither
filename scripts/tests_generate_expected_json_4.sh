#!/usr/bin/env bash

DIR="$(cd "$(dirname "$0")" && pwd)"

# generate_expected_json file.sol detectors
generate_expected_json(){
    # generate output filename
    # e.g. file: uninitialized.sol detector: uninitialized-state
    # ---> uninitialized.uninitialized-state.json
    output_filename="$(basename $1 .sol).$2.json"

    # run slither detector on input file and save output as json
    slither "$1" --solc-disable-warnings --detect "$2" --json "$DIR/../tests/expected_json/$output_filename" --solc solc-0.4.25

}


#generate_expected_json tests/deprecated_calls.sol "deprecated-standards"
#generate_expected_json tests/erc20_indexed.sol "erc20-indexed"
#generate_expected_json tests/incorrect_erc20_interface.sol "erc20-interface"
#generate_expected_json tests/uninitialized.sol "uninitialized-state"
#generate_expected_json tests/backdoor.sol "backdoor"
#generate_expected_json tests/backdoor.sol "suicidal"
#generate_expected_json tests/pragma.0.4.24.sol "pragma"
#generate_expected_json tests/old_solc.sol.json "solc-version"
#generate_expected_json tests/reentrancy.sol "reentrancy-eth"
#generate_expected_json tests/uninitialized_storage_pointer.sol "uninitialized-storage"
#generate_expected_json tests/tx_origin.sol "tx-origin"
#generate_expected_json tests/unused_state.sol "unused-state"
#generate_expected_json tests/locked_ether.sol "locked-ether"
#generate_expected_json tests/arbitrary_send.sol "arbitrary-send"
#generate_expected_json tests/inline_assembly_contract.sol "assembly"
#generate_expected_json tests/inline_assembly_library.sol "assembly"
#generate_expected_json tests/low_level_calls.sol "low-level-calls"
#generate_expected_json tests/const_state_variables.sol "constable-states"
#generate_expected_json tests/external_function.sol "external-function"
#generate_expected_json tests/external_function_2.sol "external-function"
#generate_expected_json tests/naming_convention.sol "naming-convention"
#generate_expected_json tests/uninitialized_local_variable.sol "uninitialized-local"
#generate_expected_json tests/controlled_delegatecall.sol "controlled-delegatecall"
#generate_expected_json tests/constant.sol "constant-function"
#generate_expected_json tests/unused_return.sol "unused-return"
#generate_expected_json tests/shadowing_state_variable.sol "shadowing-state"
#generate_expected_json tests/shadowing_abstract.sol "shadowing-abstract"
#generate_expected_json tests/timestamp.sol "timestamp"
#generate_expected_json tests/multiple_calls_in_loop.sol "calls-loop"
#generate_expected_json tests/shadowing_builtin_symbols.sol "shadowing-builtin"
#generate_expected_json tests/shadowing_local_variable.sol "shadowing-local"
#generate_expected_json tests/solc_version_incorrect.sol "solc-version"
generate_expected_json tests/right_to_left_override.sol "rtlo"
