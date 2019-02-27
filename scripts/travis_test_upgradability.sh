#!/usr/bin/env bash

### Test slither-check-upgradability

DIR_TESTS="tests/check-upgradability"

slither-check-upgradability "$DIR_TESTS/proxy.sol" Proxy "$DIR_TESTS/contractV1.sol" ContractV1 --solc solc-0.5.0 > test_1.txt 2>&1
DIFF=$(diff test_1.txt "$DIR_TESTS/test_1.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradability failed"
    cat test_1.txt
    cat "$DIR_TESTS/test_1.txt"
    exit -1
fi

slither-check-upgradability "$DIR_TESTS/proxy.sol" Proxy "$DIR_TESTS/contractV1.sol" ContractV1 --solc solc-0.5.0 --new-version "$DIR_TESTS/contractV2.sol" --new-contract-name ContractV2 > test_2.txt 2>&1 
DIFF=$(diff test_2.txt "$DIR_TESTS/test_2.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradability failed"
    cat test_2.txt
    cat "$DIR_TESTS/test_2.txt"
    exit -1
fi

slither-check-upgradability "$DIR_TESTS/proxy.sol" Proxy "$DIR_TESTS/contractV1.sol" ContractV1 --solc solc-0.5.0 --new-version "$DIR_TESTS/contractV2_bug.sol" --new-contract-name ContractV2 > test_3.txt 2>&1 
DIFF=$(diff test_3.txt "$DIR_TESTS/test_3.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradability failed"
    cat test_3.txt
    cat "$DIR_TESTS/test_3.txt"
    exit -1
fi

slither-check-upgradability "$DIR_TESTS/proxy.sol" Proxy "$DIR_TESTS/contractV1.sol" ContractV1 --solc solc-0.5.0 --new-version "$DIR_TESTS/contractV2_bug2.sol" --new-contract-name ContractV2 > test_4.txt 2>&1 
DIFF=$(diff test_4.txt "$DIR_TESTS/test_4.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradability failed"
    cat test_4.txt
    cat "$DIR_TESTS/test_4.txt"
    exit -1
fi

rm test_1.txt
rm test_2.txt
rm test_3.txt
rm test_4.txt
