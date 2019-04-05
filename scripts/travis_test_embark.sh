#!/usr/bin/env bash

### Test embark integration

mkdir test_embark
cd test_embark

curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
nvm install --lts
nvm use --lts

npm install embark
embark demo
cd embark_demo
npm install
slither . --embark-overwrite-config

if [ $? -eq 3 ]
then  
    echo "Embark test failed"
    exit -1
fi

