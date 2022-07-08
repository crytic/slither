#!/bin/bash

DIR_TESTS="tests/check-kspec"

solc-select use "0.5.0"
slither-check-kspec "$DIR_TESTS/safeAdd/safeAdd.sol" "$DIR_TESTS/safeAdd/spec.md" > test_1.txt 
DIFF=$(diff test_1.txt "$DIR_TESTS/test_1.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-kspec 1 failed"
    cat test_1.txt
    echo ""
    cat "$DIR_TESTS/test_1.txt"
    exit 255
fi

rm test_1.txt
