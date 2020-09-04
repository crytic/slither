#!/usr/bin/env bash

### Test

if ! slither "tests/*.json" --config "tests/config/slither.config.json"; then
    echo "Config failed"
    exit 1
fi

