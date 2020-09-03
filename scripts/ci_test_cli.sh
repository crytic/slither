#!/usr/bin/env bash

### Test

if ! slither "tests/*.json" --solc-ast --ignore-return-value; then
    echo "--solc-ast failed"
    exit 1
fi

if ! slither "tests/*0.5*.sol" --solc-disable-warnings --ignore-return-value; then
    echo "--solc-disable-warnings failed"
    exit 1
fi

if ! slither "tests/*0.5*.sol" --disable-color --ignore-return-value; then
    echo "--disable-color failed"
    exit 1
fi
