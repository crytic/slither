#!/usr/bin/env bash

# used to pass --cov=$path and --cov-append to pytest
if [ "$1" != "" ]; then
    pytest "$1" tests/tools/read-storage/test_read_storage.py
    status_code=$?
    python -m coverage report
else
    pytest tests/tools/read-storage/test_read_storage.py
    status_code=$?
fi

exit "$status_code"