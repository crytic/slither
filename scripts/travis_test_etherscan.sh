#!/usr/bin/env bash

### Test etherscan integration

mkdir etherscan
cd etherscan

wget -O solc-0.4.25 https://github.com/ethereum/solidity/releases/download/v0.4.25/solc-static-linux
chmod +x solc-0.4.25

slither 0x7F37f78cBD74481E593F9C737776F7113d76B315 --solc "./solc-0.4.25"

if [ $? -ne 6 ]
then
    echo "Etherscan test failed"
    exit -1
fi

slither rinkeby:0xFe05820C5A92D9bc906D4A46F662dbeba794d3b7 --solc "./solc-0.4.25"

if [ $? -ne 76 ]
then
    echo "Etherscan test failed"
    exit -1
fi

