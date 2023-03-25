# used to pass --cov=$path and --cov-append to pytest
pytest $1 tests/unit/
if [ "$1" != "" ]; then
    python -m coverage report
fi