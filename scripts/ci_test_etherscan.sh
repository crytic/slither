#!/usr/bin/env bash

### Test etherscan integration

mkdir etherscan
cd etherscan || exit 255

echo "::group::Etherscan mainnet"
if ! slither 0x7F37f78cBD74481E593F9C737776F7113d76B315 --etherscan-apikey "$GITHUB_ETHERSCAN"; then
    echo "Etherscan mainnet test failed"
    exit 1
fi
echo "::endgroup::"

# Perform a small sleep when API key is not available (e.g. on PR CI from external contributor)
if [ "$GITHUB_ETHERSCAN" = "" ];
    sleep $[ ( $RANDOM % 5 )  + 1 ]s
fi

echo "::group::Etherscan rinkeby"
if ! slither rinkeby:0xFe05820C5A92D9bc906D4A46F662dbeba794d3b7 --etherscan-apikey "$GITHUB_ETHERSCAN"; then
    echo "Etherscan rinkeby test failed"
    exit 1
fi
echo "::endgroup::"

exit 0

