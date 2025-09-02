#!/usr/bin/env bash

# Use UV_RUN if set (for CI), otherwise run directly (for local dev)
RUN="${UV_RUN:-}"

# used to pass --cov=$path and --cov-append to pytest
if [ "$1" != "" ]; then
    $RUN pytest "$1" tests/e2e/ -n auto
    status_code=$?
    $RUN python -m coverage report
else
    $RUN pytest tests/e2e/ -n auto
    status_code=$?
fi

exit "$status_code"
