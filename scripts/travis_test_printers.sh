#!/usr/bin/env bash

### Test printer 

slither "tests/*.json" --print all

if [ $? -ne 0 ]; then
    echo "Printer tests failed"
    exit 1
fi

