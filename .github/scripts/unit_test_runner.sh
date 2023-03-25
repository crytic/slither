#!/usr/bin/env bash

# used to pass --cov=$path and --cov-append to pytest
if [ "$1" != "" ]; then
    pytest "$1" tests/unit/
    status_code=$?
    python -m coverage report
else
    pytest tests/unit/
    status_code=$?
fi

exit "$status_code"