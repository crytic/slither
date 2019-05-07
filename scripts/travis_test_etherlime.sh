#!/usr/bin/env bash

### Test etherlime integration

mkdir test_etherlime
cd test_etherlime

curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
source ~/.nvm/nvm.sh
nvm install --lts
nvm use --lts

npm i -g etherlime
etherlime init
slither .

if [ $? -eq 6 ]
then  
    exit 0
fi

echo "Etherlime test failed"
exit -1
