#!/usr/bin/env bash

### Test slither-check-upgradeability

DIR_TESTS="tests/tools/check_upgradeability"
solc-select install "0.5.0"
solc-select use "0.5.0"

slither-check-upgradeability  "$DIR_TESTS/contractV1.sol" ContractV1 --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy  > test_1.txt 2>&1
DIFF=$(diff test_1.txt "$DIR_TESTS/test_1.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 1 failed"
    cat test_1.txt
    echo ""
    cat "$DIR_TESTS/test_1.txt"
    exit 255
fi

slither-check-upgradeability "$DIR_TESTS/contractV1.sol" ContractV1  --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy  --new-contract-filename "$DIR_TESTS/contractV2.sol" --new-contract-name ContractV2 > test_2.txt 2>&1
DIFF=$(diff test_2.txt "$DIR_TESTS/test_2.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 2 failed"
    cat test_2.txt
    echo ""
    cat "$DIR_TESTS/test_2.txt"
    exit 255
fi

slither-check-upgradeability "$DIR_TESTS/contractV1.sol" ContractV1 --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy  --new-contract-filename "$DIR_TESTS/contractV2_bug.sol" --new-contract-name ContractV2 > test_3.txt 2>&1
DIFF=$(diff test_3.txt "$DIR_TESTS/test_3.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 3 failed"
    cat test_3.txt
    echo ""
    cat "$DIR_TESTS/test_3.txt"
    exit 255
fi

slither-check-upgradeability "$DIR_TESTS/contractV1.sol" ContractV1 --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy  --new-contract-filename "$DIR_TESTS/contractV2_bug2.sol" --new-contract-name ContractV2 > test_4.txt 2>&1
DIFF=$(diff test_4.txt "$DIR_TESTS/test_4.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 4 failed"
    cat test_4.txt
    echo ""
    cat "$DIR_TESTS/test_4.txt"
    exit 255
fi

slither-check-upgradeability "$DIR_TESTS/contract_initialization.sol" Contract_no_bug --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy   > test_5.txt 2>&1
DIFF=$(diff test_5.txt "$DIR_TESTS/test_5.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 5 failed"
    cat test_5.txt
    echo ""
    cat "$DIR_TESTS/test_5.txt"
    echo ""
    echo "$DIFF"
    exit 255
fi

slither-check-upgradeability "$DIR_TESTS/contract_initialization.sol" Contract_no_bug --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy   > test_5.txt 2>&1
DIFF=$(diff test_5.txt "$DIR_TESTS/test_5.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 5 failed"
    cat test_5.txt
    echo ""
    cat "$DIR_TESTS/test_5.txt"
    echo ""
    echo "$DIFF"
    exit 255
fi


slither-check-upgradeability "$DIR_TESTS/contract_initialization.sol" Contract_lack_to_call_modifier --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy   > test_6.txt 2>&1
DIFF=$(diff test_6.txt "$DIR_TESTS/test_6.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 6 failed"
    cat test_6.txt
    echo ""
    cat "$DIR_TESTS/test_6.txt"
    echo ""
    echo "$DIFF"
    exit 255
fi


slither-check-upgradeability "$DIR_TESTS/contract_initialization.sol" Contract_not_called_super_init --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy   > test_7.txt 2>&1
DIFF=$(diff test_7.txt "$DIR_TESTS/test_7.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 7 failed"
    cat test_7.txt
    echo ""
    cat "$DIR_TESTS/test_7.txt"
    echo ""
    echo "$DIFF"
    exit 255
fi

slither-check-upgradeability "$DIR_TESTS/contract_initialization.sol" Contract_no_bug_inherits --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy   > test_8.txt 2>&1
DIFF=$(diff test_8.txt "$DIR_TESTS/test_8.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 8 failed"
    cat test_8.txt
    echo ""
    cat "$DIR_TESTS/test_8.txt"
    echo ""
    echo "$DIFF"
    exit 255
fi

slither-check-upgradeability "$DIR_TESTS/contract_initialization.sol" Contract_double_call --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy   > test_9.txt 2>&1
DIFF=$(diff test_9.txt "$DIR_TESTS/test_9.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 9 failed"
    cat test_9.txt
    echo ""
    cat "$DIR_TESTS/test_9.txt"
    echo ""
    echo "$DIFF"
    exit 255
fi

slither-check-upgradeability "$DIR_TESTS/contractV1.sol" ContractV1  --new-contract-filename "$DIR_TESTS/contract_v2_constant.sol" --new-contract-name ContractV2 > test_10.txt 2>&1
DIFF=$(diff test_10.txt "$DIR_TESTS/test_10.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 10 failed"
    cat test_10.txt
    echo ""
    cat "$DIR_TESTS/test_10.txt"
    echo ""
    echo "$DIFF"
    exit 255
fi

slither-check-upgradeability "$DIR_TESTS/contract_v1_var_init.sol" ContractV1   > test_11.txt 2>&1
DIFF=$(diff test_11.txt "$DIR_TESTS/test_11.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 11 failed"
    cat test_11.txt
    echo ""
    cat "$DIR_TESTS/test_11.txt"
    echo ""
    echo "$DIFF"
    exit 255
fi

slither-check-upgradeability "$DIR_TESTS/contractV1_struct.sol" ContractV1 --new-contract-filename "$DIR_TESTS/contractV2_struct.sol" --new-contract-name ContractV2   > test_12.txt 2>&1
DIFF=$(diff test_12.txt "$DIR_TESTS/test_12.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 12 failed"
    cat test_12.txt
    echo ""
    cat "$DIR_TESTS/test_12.txt"
    echo ""
    echo "$DIFF"
    exit 255
fi

slither-check-upgradeability "$DIR_TESTS/contractV1_struct.sol" ContractV1 --new-contract-filename "$DIR_TESTS/contractV2_struct_bug.sol" --new-contract-name ContractV2   > test_13.txt 2>&1
DIFF=$(diff test_13.txt "$DIR_TESTS/test_13.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 13 failed"
    cat test_13.txt
    echo ""
    cat "$DIR_TESTS/test_13.txt"
    echo ""
    echo "$DIFF"
    exit 255
fi

slither-check-upgradeability "$DIR_TESTS/contract_initialization.sol" Contract_no_bug_reinitializer --proxy-filename "$DIR_TESTS/proxy.sol" --proxy-name Proxy   > test_14.txt 2>&1
DIFF=$(diff test_14.txt "$DIR_TESTS/test_14.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 14 failed"
    cat test_14.txt
    echo ""
    cat "$DIR_TESTS/test_14.txt"
    echo ""
    echo "$DIFF"
    exit 255
fi

slither-check-upgradeability "$DIR_TESTS/contract_initialization.sol" Contract_reinitializer_V2 --new-contract-name Counter_reinitializer_V3_V4 > test_15.txt 2>&1
DIFF=$(diff test_15.txt "$DIR_TESTS/test_15.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-check-upgradeability 14 failed"
    cat test_15.txt
    echo ""
    cat "$DIR_TESTS/test_15.txt"
    echo ""
    echo "$DIFF"
    exit 255
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
rm test_12.txt
rm test_13.txt
rm test_14.txt
rm test_15.txt
