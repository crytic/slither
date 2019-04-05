#!/usr/bin/env bash

### Test slither-check-upgradeability

DIR_TESTS="tests/check-upgradeability"

slither-check-upgradeability "$DIR_TESTS/proxy.sol" Proxy "$DIR_TESTS/contractV1.sol" ContractV1 --solc solc-0.5.0 > test_1.txt 2>&1
DIFF=$(diff test_1.txt "$DIR_TESTS/test_1.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradeability failed"
    cat test_1.txt
    cat "$DIR_TESTS/test_1.txt"
    exit -1
fi

slither-check-upgradeability "$DIR_TESTS/proxy.sol" Proxy "$DIR_TESTS/contractV1.sol" ContractV1 --solc solc-0.5.0 --new-version "$DIR_TESTS/contractV2.sol" --new-contract-name ContractV2 > test_2.txt 2>&1 
DIFF=$(diff test_2.txt "$DIR_TESTS/test_2.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradeability failed"
    cat test_2.txt
    cat "$DIR_TESTS/test_2.txt"
    exit -1
fi

slither-check-upgradeability "$DIR_TESTS/proxy.sol" Proxy "$DIR_TESTS/contractV1.sol" ContractV1 --solc solc-0.5.0 --new-version "$DIR_TESTS/contractV2_bug.sol" --new-contract-name ContractV2 > test_3.txt 2>&1 
DIFF=$(diff test_3.txt "$DIR_TESTS/test_3.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradeability failed"
    cat test_3.txt
    cat "$DIR_TESTS/test_3.txt"
    exit -1
fi

slither-check-upgradeability "$DIR_TESTS/proxy.sol" Proxy "$DIR_TESTS/contractV1.sol" ContractV1 --solc solc-0.5.0 --new-version "$DIR_TESTS/contractV2_bug2.sol" --new-contract-name ContractV2 > test_4.txt 2>&1 
DIFF=$(diff test_4.txt "$DIR_TESTS/test_4.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradeability failed"
    cat test_4.txt
    cat "$DIR_TESTS/test_4.txt"
    exit -1
fi

slither-check-upgradeability "$DIR_TESTS/proxy.sol" Proxy "$DIR_TESTS/contract_initialization.sol" Contract_no_bug --solc solc-0.5.0 > test_5.txt 2>&1 
DIFF=$(diff test_5.txt "$DIR_TESTS/test_5.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradeability failed"
    cat test_5.txt
    cat "$DIR_TESTS/test_5.txt"
    exit -1
fi

rm test_1.txt
rm test_2.txt
rm test_3.txt
rm test_4.txt
rm test_5.txt

