#!/usr/bin/env bash

### Test truffle integration

mkdir test_truffle
cd test_truffle || exit 255

curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
# shellcheck disable=SC1090
source ~/.nvm/nvm.sh
nvm install --lts
nvm use --lts

npm install -g truffle
truffle unbox metacoin
slither .

if [ $? -eq 8 ]
then
    exit 0
fi

echo "Truffle test failed"
exit 255
