#!/usr/bin/env bash

# generate_expected_json file.sol detectors
generate_expected_json(){
    # generate output filename
    # e.g. file: uninitialized.sol detector: uninitialized-state
    # ---> uninitialized.uninitialized-state.json
    output_filename="$(basename $1 .sol).$2.json"

    # run slither detector on input file and save output as json
    slither "$1" --disable-solc-warnings --detectors "$2" --json "$output_filename"

    # beautify json and move to test/
    cat "$output_filename" | python -m json.tool > tests/$output_filename

    # rm original un-beautified json file
    rm $output_filename
}

generate_expected_json tests/uninitialized.sol "uninitialized-state"
generate_expected_json tests/backdoor.sol "backdoor"
generate_expected_json tests/backdoor.sol "suicidal"
generate_expected_json tests/pragma.0.4.24.sol "pragma"
generate_expected_json tests/old_solc.sol.json "solc-version"
generate_expected_json tests/reentrancy.sol "reentrancy"
generate_expected_json tests/uninitialized_storage_pointer.sol "uninitialized-storage"
generate_expected_json tests/tx_origin.sol "tx-origin"
generate_expected_json tests/unused_state.sol "unused-state"
generate_expected_json tests/locked_ether.sol "locked-ether"
generate_expected_json tests/arbitrary_send.sol "arbitrary-send"
generate_expected_json tests/inline_assembly_contract.sol "assembly"
generate_expected_json tests/inline_assembly_library.sol "assembly"
generate_expected_json tests/low_level_calls.sol "low-level-calls"
generate_expected_json tests/const_state_variables.sol "constable-states"
generate_expected_json tests/external_function.sol "external-function"
generate_expected_json tests/naming_convention.sol "naming-convention"
