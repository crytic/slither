#!/usr/bin/env bash

### Test slither-interface

DIR_TESTS="tests/tools/interface" 

solc-select use 0.8.19 --always-install

#Test 1 - Etherscan target
slither-interface WETH9 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2
DIFF=$(diff crytic-export/interfaces/IWETH9.sol "$DIR_TESTS/test_1.sol" --strip-trailing-cr)
if [  "$DIFF" != "" ]
then
    echo "slither-interface test 1 failed"
    cat "crytic-export/interfaces/IWETH9.sol"
    echo ""
    cat "$DIR_TESTS/test_1.sol"
    exit 255
fi


#Test 2 - Local file target
slither-interface Mock tests/tools/interface/ContractMock.sol
DIFF=$(diff crytic-export/interfaces/IMock.sol "$DIR_TESTS/test_2.sol" --strip-trailing-cr)
if [  "$DIFF" != "" ]
then
    echo "slither-interface test 2 failed"
    cat "crytic-export/interfaces/IMock.sol"
    echo ""
    cat "$DIR_TESTS/test_2.sol"
    exit 255
fi


#Test 3 - unroll structs
slither-interface Mock tests/tools/interface/ContractMock.sol --unroll-structs
DIFF=$(diff crytic-export/interfaces/IMock.sol "$DIR_TESTS/test_3.sol" --strip-trailing-cr)
if [  "$DIFF" != "" ]
then
    echo "slither-interface test 3 failed"
    cat "crytic-export/interfaces/IMock.sol"
    echo ""
    cat "$DIR_TESTS/test_3.sol"
    exit 255
fi

#Test 4 - exclude structs
slither-interface Mock tests/tools/interface/ContractMock.sol --exclude-structs
DIFF=$(diff crytic-export/interfaces/IMock.sol "$DIR_TESTS/test_4.sol" --strip-trailing-cr)
if [  "$DIFF" != "" ]
then
    echo "slither-interface test 4 failed"
    cat "crytic-export/interfaces/IMock.sol"
    echo ""
    cat "$DIR_TESTS/test_4.sol"
    exit 255
fi

#Test 5 - exclude errors
slither-interface Mock tests/tools/interface/ContractMock.sol --exclude-errors
DIFF=$(diff crytic-export/interfaces/IMock.sol "$DIR_TESTS/test_5.sol" --strip-trailing-cr)
if [  "$DIFF" != "" ]
then
    echo "slither-interface test 5 failed"
    cat "crytic-export/interfaces/IMock.sol"
    echo ""
    cat "$DIR_TESTS/test_5.sol"
    exit 255
fi

#Test 6 - exclude enums
slither-interface Mock tests/tools/interface/ContractMock.sol --exclude-enums
DIFF=$(diff crytic-export/interfaces/IMock.sol "$DIR_TESTS/test_6.sol" --strip-trailing-cr)
if [  "$DIFF" != "" ]
then
    echo "slither-interface test 6 failed"
    cat "crytic-export/interfaces/IMock.sol"
    echo ""
    cat "$DIR_TESTS/test_6.sol"
    exit 255
fi

#Test 7 - exclude events
slither-interface Mock tests/tools/interface/ContractMock.sol --exclude-events
DIFF=$(diff crytic-export/interfaces/IMock.sol "$DIR_TESTS/test_7.sol" --strip-trailing-cr)
if [  "$DIFF" != "" ]
then
    echo "slither-interface test 7 failed"
    cat "crytic-export/interfaces/IMock.sol"
    echo ""
    cat "$DIR_TESTS/test_7.sol"
    exit 255
fi

rm -r crytic-export