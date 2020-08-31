#!/usr/bin/env bash

source "$(dirname "$0")""/ci_test.sh"

solc use "0.6.11"

# Be sure that only one of the following line is uncommented before running the script


#generate_expected_json tests/filename.sol "detector_name"

