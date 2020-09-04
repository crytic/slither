#!/usr/bin/env bash

### Test etherscan integration

mkdir etherscan
cd etherscan || exit 255

slither 0x7F37f78cBD74481E593F9C737776F7113d76B315 --etherscan-apikey "$GITHUB_ETHERSCAN"

if [ $? -ne 5 ]
then
    echo "Etherscan test failed"
    exit 255
fi

slither rinkeby:0xFe05820C5A92D9bc906D4A46F662dbeba794d3b7 --etherscan-apikey "$GITHUB_ETHERSCAN"

if [ $? -ne 70 ]
then
    echo "Etherscan test failed"
    exit 255
fi

