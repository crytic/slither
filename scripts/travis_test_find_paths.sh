#!/usr/bin/env bash

### Test slither-check-upgradability

DIR_TESTS="tests/possible_paths"

slither-find-paths "$DIR_TESTS/paths.sol"  A.destination --solc solc-0.5.0 > test_possible_paths.txt 2>&1
DIFF=$(diff test_possible_paths.txt "$DIR_TESTS/paths.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-find-paths failed"
    cat test_possible_paths.txt
    cat "$DIR_TESTS/paths.txt"
    exit -1
fi
rm test_possible_paths.txt
