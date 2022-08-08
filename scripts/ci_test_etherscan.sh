#!/usr/bin/env bash

### Test etherscan integration

mkdir etherscan
cd etherscan || exit 255

if slither 0x7F37f78cBD74481E593F9C737776F7113d76B315 --etherscan-apikey "$GITHUB_ETHERSCAN"; then
    echo "Etherscan test failed"
    exit 1
fi

if slither rinkeby:0xFe05820C5A92D9bc906D4A46F662dbeba794d3b7 --etherscan-apikey "$GITHUB_ETHERSCAN"; then
    echo "Etherscan test failed"
    exit 1
fi

exit 0

