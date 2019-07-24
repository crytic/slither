#!/usr/bin/env bash

DIR="$(cd "$(dirname "$0")" && pwd)"
CURRENT_PATH=$(pwd)
TRAVIS_PATH='/home/travis/build/crytic/slither'


# generate_expected_json file.sol detectors
generate_expected_json(){
    # generate output filename
    # e.g. file: uninitialized.sol detector: uninitialized-state
    # ---> uninitialized.uninitialized-state.json
    output_filename="$DIR/../tests/expected_json/$(basename $1 .sol).$2.json"
    output_filename_txt="$DIR/../tests/expected_json/$(basename $1 .sol).$2.txt"

    # run slither detector on input file and save output as json
    slither "$1" --solc-disable-warnings --detect "$2" --json "$output_filename" --solc solc-0.5.1 > $output_filename_txt 2>&1 

    sed "s|$CURRENT_PATH|$TRAVIS_PATH|g" "$output_filename" -i
    sed "s|$CURRENT_PATH|$TRAVIS_PATH|g" "$output_filename_txt" -i
}

generate_expected_json tests/void-cst.sol "void-cst"
#generate_expected_json tests/solc_version_incorrect_05.ast.json "solc-version"
#generate_expected_json tests/uninitialized-0.5.1.sol "uninitialized-state"
#generate_expected_json tests/backdoor.sol "backdoor"
#generate_expected_json tests/backdoor.sol "suicidal"
#generate_expected_json tests/old_solc.sol.json "solc-version"
#generate_expected_json tests/reentrancy-0.5.1.sol "reentrancy-eth"
#generate_expected_json tests/tx_origin-0.5.1.sol "tx-origin"
#generate_expected_json tests/locked_ether-0.5.1.sol "locked-ether"
#generate_expected_json tests/arbitrary_send-0.5.1.sol "arbitrary-send"
#generate_expected_json tests/inline_assembly_contract-0.5.1.sol "assembly"
#generate_expected_json tests/inline_assembly_library-0.5.1.sol "assembly"
#generate_expected_json tests/constant-0.5.1.sol "constant-function"
#generate_expected_json tests/incorrect_equality.sol "incorrect-equality"
#generate_expected_json tests/too_many_digits.sol "too-many-digits"
#generate_expected_json tests/unchecked_lowlevel-0.5.1.sol "unchecked-lowlevel"
#generate_expected_json tests/unchecked_send-0.5.1.sol "unchecked-send"

