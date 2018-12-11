#!/usr/bin/env bash
python setup.py install
# Used by travis_test.sh
pip install deepdiff

function install_solc {
    sudo wget -O /usr/bin/solc-0.4.25 https://github.com/ethereum/solidity/releases/download/v0.4.25/solc-static-linux
    sudo chmod +x /usr/bin/solc-0.4.25
    sudo wget -O /usr/bin/solc-0.5.1 https://github.com/ethereum/solidity/releases/download/v0.5.1/solc-static-linux
    sudo chmod +x /usr/bin/solc-0.5.1
}

install_solc
