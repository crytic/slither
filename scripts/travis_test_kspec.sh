#!/bin/bash

DIR_TESTS="tests/check-kspec"

slither-check-kspec "$DIR_TESTS/safeAdd/safeAdd.sol" "$DIR_TESTS/safeAdd/spec.md" --solc solc-0.5.0 > test_1.txt 2>&1
DIFF=$(diff test_1.txt "$DIR_TESTS/test_1.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradeability 1 failed"
    cat test_1.txt
    echo ""
    cat "$DIR_TESTS/test_1.txt"
    exit -1
fi

rm test_1.txt
