#!/usr/bin/env bash

### Test slither-check-upgradeability

DIR_TESTS="tests/check-upgradeability"

slither-check-upgradeability  "$DIR_TESTS/contractV1.sol" ContractV1 --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy --solc solc-0.5.0 > test_1.txt 2>&1
DIFF=$(diff test_1.txt "$DIR_TESTS/test_1.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradeability 1 failed"
    cat test_1.txt
    echo ""
    cat "$DIR_TESTS/test_1.txt"
    exit -1
fi

slither-check-upgradeability "$DIR_TESTS/contractV1.sol" ContractV1  --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy --solc solc-0.5.0 --new-contract-filename "$DIR_TESTS/contractV2.sol" --new-contract-name ContractV2 > test_2.txt 2>&1
DIFF=$(diff test_2.txt "$DIR_TESTS/test_2.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradeability 2 failed"
    cat test_2.txt
    echo ""
    cat "$DIR_TESTS/test_2.txt"
    exit -1
fi

slither-check-upgradeability "$DIR_TESTS/contractV1.sol" ContractV1 --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy --solc solc-0.5.0 --new-contract-filename "$DIR_TESTS/contractV2_bug.sol" --new-contract-name ContractV2 > test_3.txt 2>&1
DIFF=$(diff test_3.txt "$DIR_TESTS/test_3.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradeability 3 failed"
    cat test_3.txt
    echo ""
    cat "$DIR_TESTS/test_3.txt"
    exit -1
fi

slither-check-upgradeability "$DIR_TESTS/contractV1.sol" ContractV1 --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy --solc solc-0.5.0 --new-contract-filename "$DIR_TESTS/contractV2_bug2.sol" --new-contract-name ContractV2 > test_4.txt 2>&1
DIFF=$(diff test_4.txt "$DIR_TESTS/test_4.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradeability 4 failed"
    cat test_4.txt
    echo ""
    cat "$DIR_TESTS/test_4.txt"
    exit -1
fi

slither-check-upgradeability "$DIR_TESTS/contract_initialization.sol" Contract_no_bug --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy  --solc solc-0.5.0 > test_5.txt 2>&1
DIFF=$(diff test_5.txt "$DIR_TESTS/test_5.txt")
if [  "$DIFF" != "" ] 
then
    echo "slither-check-upgradeability 5 failed"
    cat test_5.txt
    echo ""
    cat "$DIR_TESTS/test_5.txt"
    echo ""
    echo "$DIFF"
    exit -1
fi

slither-check-upgradeability "$DIR_TESTS/contract_initialization.sol" Contract_no_bug --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy  --solc solc-0.5.0 > test_5.txt 2>&1
DIFF=$(diff test_5.txt "$DIR_TESTS/test_5.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 5 failed"
    cat test_5.txt
    echo ""
    cat "$DIR_TESTS/test_5.txt"
    echo ""
    echo "$DIFF"
    exit -1
fi


slither-check-upgradeability "$DIR_TESTS/contract_initialization.sol" Contract_lack_to_call_modifier --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy  --solc solc-0.5.0 > test_6.txt 2>&1
DIFF=$(diff test_6.txt "$DIR_TESTS/test_6.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 6 failed"
    cat test_6.txt
    echo ""
    cat "$DIR_TESTS/test_6.txt"
    echo ""
    echo "$DIFF"
    exit -1
fi


slither-check-upgradeability "$DIR_TESTS/contract_initialization.sol" Contract_not_called_super_init --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy  --solc solc-0.5.0 > test_7.txt 2>&1
DIFF=$(diff test_7.txt "$DIR_TESTS/test_7.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 7 failed"
    cat test_7.txt
    echo ""
    cat "$DIR_TESTS/test_7.txt"
    echo ""
    echo "$DIFF"
    exit -1
fi

slither-check-upgradeability "$DIR_TESTS/contract_initialization.sol" Contract_no_bug_inherits --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy  --solc solc-0.5.0 > test_8.txt 2>&1
DIFF=$(diff test_8.txt "$DIR_TESTS/test_8.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 8 failed"
    cat test_8.txt
    echo ""
    cat "$DIR_TESTS/test_8.txt"
    echo ""
    echo "$DIFF"
    exit -1
fi

slither-check-upgradeability "$DIR_TESTS/contract_initialization.sol" Contract_double_call --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy  --solc solc-0.5.0 > test_9.txt 2>&1
DIFF=$(diff test_9.txt "$DIR_TESTS/test_9.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 9 failed"
    cat test_9.txt
    echo ""
    cat "$DIR_TESTS/test_9.txt"
    echo ""
    echo "$DIFF"
    exit -1
fi

slither-check-upgradeability "$DIR_TESTS/contractV1.sol" ContractV1 --solc solc-0.5.0 --new-contract-filename "$DIR_TESTS/contract_v2_constant.sol" --new-contract-name ContractV2 > test_10.txt 2>&1
DIFF=$(diff test_10.txt "$DIR_TESTS/test_10.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 10 failed"
    cat test_10.txt
    echo ""
    cat "$DIR_TESTS/test_10.txt"
    echo ""
    echo "$DIFF"
    exit -1
fi

slither-check-upgradeability "$DIR_TESTS/contract_v1_var_init.sol" ContractV1 --solc solc-0.5.0  > test_11.txt 2>&1
DIFF=$(diff test_11.txt "$DIR_TESTS/test_11.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 11 failed"
    cat test_11.txt
    echo ""
    cat "$DIR_TESTS/test_11.txt"
    echo ""
    echo "$DIFF"
    exit -1
fi

rm test_1.txt
rm test_2.txt
rm test_3.txt
rm test_4.txt
rm test_5.txt
rm test_6.txt
rm test_7.txt
rm test_8.txt
rm test_9.txt
rm test_10.txt
rm test_11.txt
