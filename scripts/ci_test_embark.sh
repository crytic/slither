#!/usr/bin/env bash

### Test embark integration

mkdir test_embark
cd test_embark || exit 255

NVM_METHOD=script

install_node()
{
    if [[ -z "$NODEVER" ]]; then
        NODEVER="node"
        echo "[-] NODEVER was not set, using the latest version."
    fi
    wget -q -O nvm-install.sh https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh
    if [ ! "fabc489b39a5e9c999c7cab4d281cdbbcbad10ec2f8b9a7f7144ad701b6bfdc7  nvm-install.sh" = "$(sha256sum nvm-install.sh)" ]; then
        echo "NVM installer does not match expected checksum! exiting"
        exit 1
    fi
    bash nvm-install.sh
    rm nvm-install.sh

    # Avoid picking up `.nvmrc` from the repository
    pushd / >/dev/null
    . ~/.nvm/nvm.sh
    nvm install "$NODEVER"
    popd >/dev/null
}

install_node

npm install -g embark
embark demo
cd embark_demo || exit 255
npm install
slither . --embark-overwrite-config

if [ $? -eq 4 ]
then
    exit 0
fi

echo "Embark test failed"
exit 255

