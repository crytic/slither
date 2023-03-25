#!/usr/bin/env bash

# setup hardhat for compilation tests
pushd tests/e2e/compilation/test_data/test_node_modules/ || exit
npm install hardhat
popd || exit

# used to pass --cov=$path and --cov-append to pytest
pytest "$1" tests/e2e/ -n auto
if [ "$1" != "" ]; then
    python -m coverage report
fi

