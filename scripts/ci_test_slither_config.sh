#!/usr/bin/env bash

### Test

if ! slither --config-file "tests/config/slither.config.json" detect "tests/*.json"; then
    echo "Config failed"
    exit 1
fi

