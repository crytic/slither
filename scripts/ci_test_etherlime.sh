#!/usr/bin/env bash

### Test etherlime integration

mkdir test_etherlime
cd test_etherlime || exit 255

curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
# shellcheck disable=SC1090
source ~/.nvm/nvm.sh
nvm install 10.17.0
nvm use 10.17.0

npm i -g etherlime
etherlime init
slither .

if [ $? -eq 7 ]
then
    exit 0
fi

echo "Etherlime test failed"
exit 255
