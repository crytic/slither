#!/usr/bin/env bash

### Test Dapp integration

mkdir test_dapp
cd test_dapp

curl https://nixos.org/nix/install | sh
. "$HOME/.nix-profile/etc/profile.d/nix.sh"
nix-env -iA nixpkgs.cachix
cachix use dapp

git clone --recursive https://github.com/dapphub/dapptools $HOME/.dapp/dapptools
nix-env -f $HOME/.dapp/dapptools -iA dapp seth solc hevm ethsign

dapp init

slither .

if [ $? -eq 23 ]
then  
    exit 0
fi

echo "Truffle test failed"
exit -1
