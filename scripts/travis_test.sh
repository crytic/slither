#!/usr/bin/env bash

./slither.py examples/bugs --disable-solc-warnings
if [ $? -ne 2 ]; then
    exit 1
fi

exit 0
