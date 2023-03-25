#!/usr/bin/env bash

npm install --global ganache
# used to pass --cov=$path and --cov-append to pytest
pytest $1 tests/tools/read-storage/test_read_storage.py
if [ "$1" != "" ]; then
    python -m coverage report
fi