#!/usr/bin/env bash
python setup.py install
# Used by travis_test.sh
pip install deepdiff

function install_solc {
    sudo wget -O /usr/bin/solc https://github.com/ethereum/solidity/releases/download/v0.4.24/solc-static-linux
    sudo chmod +x /usr/bin/solc
}

install_solc
