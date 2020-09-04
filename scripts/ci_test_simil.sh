#!/usr/bin/env bash

### Install requisites

pip3.6 install pybind11
pip3.6 install https://github.com/facebookresearch/fastText/archive/0.2.0.zip

### Test slither-simil

solc use "0.4.25"

DIR_TESTS="tests/simil"
slither-simil info "" --filename $DIR_TESTS/../complex_func.sol --fname Complex.complexExternalWrites  > test_1.txt 2>&1
DIFF=$(diff test_1.txt "$DIR_TESTS/test_1.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-simil failed"
    cat test_1.txt
    cat "$DIR_TESTS/test_1.txt"
    exit 255
fi

rm test_1.txt
