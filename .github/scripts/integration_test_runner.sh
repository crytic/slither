# setup hardhat for compilation tests
pushd tests/e2e/compilation/test_data/test_node_modules/
npm install hardhat
popd

# used to pass --cov=$path and --cov-append to pytest
pytest $1 tests/e2e/ -n auto
python -m coverage report
