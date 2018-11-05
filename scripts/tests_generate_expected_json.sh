#!/usr/bin/env bash

DIR="$(cd "$(dirname "$0")" && pwd)"

# generate_expected_json file.sol detectors
generate_expected_json(){
    # generate output filename
    # e.g. file: uninitialized.sol detector: uninitialized-state
    # ---> uninitialized.uninitialized-state.json
    output_filename="$(basename $1 .sol).$2.json"

    # run slither detector on input file and save output as json
    slither "$1" --disable-solc-warnings --detectors "$2" --json "$DIR/tmp-gen.json"

    # convert json file to pretty print and write to destination folder
    python "$DIR/pretty_print_and_sort_json.py" "$DIR/tmp-gen.json" "$DIR/../tests/expected_json/$output_filename"

    # remove the raw un-prettified json file
    rm "$DIR/tmp-gen.json"
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
