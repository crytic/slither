Slither can be used as a library to create new utilities.
Official utils are present in [tools](https://github.com/crytic/slither/tree/master/slither/tools)

We recommend following the [developper installation](https://github.com/crytic/slither/wiki/Developer-installation).

## Skeleton
The skeleton util is present in [tools/demo](https://github.com/crytic/slither/tree/master/slither/tools/demo)

## Integration

To enable an util from the command line, update `entry_points` in [setup.py](https://github.com/crytic/slither/blob/master/setup.py).
Installing Slither will then install the util.

## Guidelines

- Favor the `logging` module rather than `print`
- Favor raising an exception rather than `sys.exit`
- Add unit-tests (ex: [scripts/travis_test_find_paths.sh](https://github.com/crytic/slither/blob/master/scripts/ci_test_find_paths.sh))

## Getting Help
Join our [slack channel](https://empireslacking.herokuapp.com/) to get any help (#ethereum).
