#!/usr/bin/env bash

source "$(dirname "$0")""/ci_test.sh"

solc use "0.6.11"

# test_slither tests/filename.sol "detector_name"
