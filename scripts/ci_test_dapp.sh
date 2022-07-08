#!/usr/bin/env bash

### Test Dapp integration

mkdir test_dapp
cd test_dapp || exit 255
# The dapp init process makes a temporary local git repo and needs certain values to be set
git config --global user.email "ci@trailofbits.com"
git config --global user.name "CI User"

which nix-env || exit 255

git clone --recursive https://github.com/dapphub/dapptools "$HOME/.dapp/dapptools"
nix-env -f "$HOME/.dapp/dapptools" -iA dapp seth solc hevm ethsign

dapp init

slither . --fail-pedantic

if [ $? -ne 255 ]
then
    echo "Truffle test failed"
    exit 255
fi

