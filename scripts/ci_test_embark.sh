#!/usr/bin/env bash

### Test embark integration

mkdir test_embark
cd test_embark || exit 255

curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
# shellcheck disable=SC1090
source ~/.nvm/nvm.sh
nvm install 10.17.0
nvm use 10.17.0

npm install -g embark@4.2.0
embark demo
cd embark_demo || exit 255
npm install

if slither . --embark-overwrite-config; then
    echo "Embark test failed"
    exit 255
fi

exit 0
