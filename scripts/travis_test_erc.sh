#!/usr/bin/env bash

### Test slither-check-erc

DIR_TESTS="tests/check-erc"

slither-check-erc "$DIR_TESTS/erc20.sol" ERC20 --solc solc-0.5.0 > test_1.txt 2>&1
DIFF=$(diff test_1.txt "$DIR_TESTS/test_1.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-erc 1 failed"
    cat test_1.txt
    echo ""
    cat "$DIR_TESTS/test_1.txt"
    exit 255
fi


rm test_1.txt
