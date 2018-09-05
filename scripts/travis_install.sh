#!/usr/bin/env bash
pip install -r requirements.txt

function install_solc {
    sudo wget -O /usr/bin/solc https://github.com/ethereum/solidity/releases/download/v0.4.23/solc-static-linux
    sudo chmod +x /usr/bin/solc
}

install_solc
