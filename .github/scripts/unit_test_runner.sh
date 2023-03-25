# used to pass --cov=$path and --cov-append to pytest
pytest $1 tests/unit/
python -m coverage report