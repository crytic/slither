#!/usr/bin/env bash

### Test etherscan integration

mkdir etherscan
cd etherscan || exit 255

echo "::group::Etherscan mainnet"
if ! slither 0x7F37f78cBD74481E593F9C737776F7113d76B315 --etherscan-apikey "$GITHUB_ETHERSCAN" --no-fail-pedantic; then
    echo "Etherscan mainnet test failed"
    exit 1
fi
echo "::endgroup::"

# Perform a small sleep when API key is not available (e.g. on PR CI from external contributor)
if [ "$GITHUB_ETHERSCAN" = "" ]; then
    sleep $(( ( RANDOM % 5 )  + 1 ))s
fi

exit 0

