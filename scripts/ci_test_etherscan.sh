#!/usr/bin/env bash
set -euo pipefail

### Test etherscan integration

# Skip when API key is not present
if [ "$GITHUB_ETHERSCAN" = "" ]; then
    echo "Skipped, no Etherscan API key provided"
    exit
fi

mkdir etherscan
cd etherscan || exit 255

echo "::group::Etherscan mainnet"
if ! slither 0x7F37f78cBD74481E593F9C737776F7113d76B315 --etherscan-apikey "$GITHUB_ETHERSCAN" --no-fail-pedantic; then
    echo "Etherscan mainnet test failed"
    exit 1
fi
echo "::endgroup::"

exit 0

