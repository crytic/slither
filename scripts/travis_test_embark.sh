#!/usr/bin/env bash

### Test embark integration

mkdir test_embark
cd test_embark

curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
source ~/.nvm/nvm.sh
nvm install 10.17.0
nvm use 10.17.0

npm install -g embark@4.2.0
embark demo
cd embark_demo
npm install
slither . --embark-overwrite-config

if [ $? -eq 3 ]
then  
    exit 0
fi

echo "Embark test failed"
exit -1

