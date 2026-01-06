#!/usr/bin/env bash
set -euo pipefail

# Source common CI test setup
source "$(dirname "$0")/ci_test_common.sh"

### Install requisites

if [ "$UV_PYTHON" = "" ]; then
    PIP="pip3"
else
    PIP="uv pip"
fi
$PIP install fasttext

### Test slither-simil

solc-select use "0.4.25"

DIR_TESTS="tests/tools/simil"
slither-simil info "" --filename $DIR_TESTS/../../unit/core/test_data/complex_func.sol --fname Complex.complexExternalWrites 2>&1 | tee test_1.txt
DIFF=$(diff test_1.txt "$DIR_TESTS/test_1.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-simil failed"
    cat test_1.txt
    cat "$DIR_TESTS/test_1.txt"
    exit 255
fi

rm test_1.txt
