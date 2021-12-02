#!/usr/bin/env bash

### Test slither-read-storage
DIR_TESTS="tests/storage-layout/read-storage"
TEST_FILE="tests/storage-layout/storage_layout-0.8.10.sol"

slither-read-storage rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 ALPHA --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_1.txt 2>&1
DIFF=$(diff test_1.txt "$DIR_TESTS/test_1.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 1 failed"
    cat test_1.txt
    echo ""
    cat "$DIR_TESTS/test_1.txt"
    exit 255
fi
rm test_1.txt

slither-read-storage rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 BETA --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_2.txt 2>&1
DIFF=$(diff test_2.txt "$DIR_TESTS/test_2.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 2 failed"
    cat test_2.txt
    echo ""
    cat "$DIR_TESTS/test_2.txt"
    exit 255
fi
rm test_2.txt

slither-read-storage rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 GAMMA --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_3.txt 2>&1
DIFF=$(diff test_3.txt "$DIR_TESTS/test_3.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 3 failed"
    cat test_3.txt
    echo ""
    cat "$DIR_TESTS/test_3.txt"
    exit 255
fi
rm test_3.txt

slither-read-storage rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 ZETA --key 1 --struct-var a --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_4.txt 2>&1
DIFF=$(diff test_4.txt "$DIR_TESTS/test_4.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 4 failed"
    cat test_4.txt
    echo ""
    cat "$DIR_TESTS/test_4.txt"
    exit 255
fi
rm test_4.txt

slither-read-storage rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 ZETA --key 1 --struct-var b --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_5.txt 2>&1
DIFF=$(diff test_5.txt "$DIR_TESTS/test_5.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 5 failed"
    cat test_5.txt
    echo ""
    cat "$DIR_TESTS/test_5.txt"
    exit 255
fi
rm test_5.txt

slither-read-storage rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 ETA --key 0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 --deep-key 1 --struct-var a --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_6.txt 2>&1 
DIFF=$(diff test_6.txt "$DIR_TESTS/test_6.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 6 failed"
    cat test_6.txt
    echo ""
    cat "$DIR_TESTS/test_6.txt"
    exit 255
fi
rm test_6.txt

slither-read-storage rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 ETA --key 0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 --deep-key 1 --struct-var b --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_7.txt 2>&1
DIFF=$(diff test_7.txt "$DIR_TESTS/test_7.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 7 failed"
    cat test_7.txt
    echo ""
    cat "$DIR_TESTS/test_7.txt"
    exit 255
fi
rm test_7.txt

slither-read-storage rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 IOTA --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_8.txt 2>&1
DIFF=$(diff test_8.txt "$DIR_TESTS/test_8.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 8 failed"
    cat test_8.txt
    echo ""
    cat "$DIR_TESTS/test_8.txt"
    exit 255
fi
rm test_8.txt

slither-read-storage rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 OMICRON --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_9.txt 2>&1
DIFF=$(diff test_9.txt "$DIR_TESTS/test_9.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 9 failed"
    cat test_9.txt
    echo ""
    cat "$DIR_TESTS/test_9.txt"
    exit 255
fi
rm test_9.txt

slither-read-storage "$TEST_FILE" rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 SIGMA --key 0 --deep-key 0 --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_10.txt 2>&1
DIFF=$(diff test_10.txt "$DIR_TESTS/test_10.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 10 failed"
    cat test_10.txt
    echo ""
    cat "$DIR_TESTS/test_10.txt"
    exit 255
fi
rm test_10.txt

slither-read-storage "$TEST_FILE" rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 SIGMA --key 0 --deep-key 1 --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_11.txt 2>&1
DIFF=$(diff test_11.txt "$DIR_TESTS/test_11.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 11 failed"
    cat test_11.txt
    echo ""
    cat "$DIR_TESTS/test_11.txt"
    exit 255
fi
rm test_11.txt

slither-read-storage "$TEST_FILE" rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 SIGMA --key 0 --deep-key 2 --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_12.txt 2>&1
DIFF=$(diff test_12.txt "$DIR_TESTS/test_12.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 12 failed"
    cat test_12.txt
    echo ""
    cat "$DIR_TESTS/test_12.txt"
    exit 255
fi
rm test_12.txt

slither-read-storage "$TEST_FILE" rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 THETA --key 0 --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_13.txt 2>&1
DIFF=$(diff test_13.txt "$DIR_TESTS/test_13.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 13 failed"
    cat test_13.txt
    echo ""
    cat "$DIR_TESTS/test_13.txt"
    exit 255
fi
rm test_13.txt

slither-read-storage "$TEST_FILE" rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 THETA --key 1 --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_14.txt 2>&1
DIFF=$(diff test_14.txt "$DIR_TESTS/test_14.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 14 failed"
    cat test_14.txt
    echo ""
    cat "$DIR_TESTS/test_14.txt"
    exit 255
fi
rm test_14.txt

slither-read-storage "$TEST_FILE" rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 THETA --key 2 --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_15.txt 2>&1
DIFF=$(diff test_15.txt "$DIR_TESTS/test_15.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 15 failed"
    cat test_15.txt
    echo ""
    cat "$DIR_TESTS/test_15.txt"
    exit 255
fi
rm test_15.txt

slither-read-storage "$TEST_FILE" rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 TAU --key 0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 --deep-key 1 --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_16.txt 2>&1
DIFF=$(diff test_16.txt "$DIR_TESTS/test_16.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 16 failed"
    cat test_16.txt
    echo ""
    cat "$DIR_TESTS/test_16.txt"
    exit 255
fi
rm test_16.txt

slither-read-storage "$TEST_FILE" rinkeby:0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 TAU --key 0x85E2B172e94Ed1d23D3bc078F327b44736887Db9 --deep-key 2 --rpc-url "$GITHUB_RPC_URL" --etherscan-apikey "$GITHUB_ETHERSCAN" > test_17.txt 2>&1
DIFF=$(diff test_17.txt "$DIR_TESTS/test_17.txt")
if [  "$DIFF" != "" ]
then
    echo "slither-read-storage 17 failed"
    cat test_17.txt
    echo ""
    cat "$DIR_TESTS/test_17.txt"
    exit 255
fi
rm test_17.txt