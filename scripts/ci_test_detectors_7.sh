#!/usr/bin/env bash

source "$(dirname "$0")""/ci_test.sh"

solc use "0.7.0"

# test_slither tests/filename.sol "detector_name"
