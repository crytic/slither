#!/usr/bin/env bash

### Test 

slither "tests/*.json" --config "tests/config/slither.config.json" 

if [ $? -ne 0 ]; then
    echo "Config failed"
    exit 1
fi

