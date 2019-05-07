#!/usr/bin/env bash

### Test slither-simil

DIR_TESTS="tests/simil"
slither-simil info "" --filename $DIR_TESTS/../complex_func.sol --contract Complex --fname complexExternalWrites --solc solc-0.4.25 > test_1.txt 2>&1
DIFF=$(diff test_1.txt "$DIR_TESTS/test_1.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-simil failed"
    cat test_1.txt
    cat "$DIR_TESTS/test_1.txt"
    exit -1
fi

rm test_1.txt
