# Testing printers

The printers are tested with files from the test data of `solc_parsing/compile` directory.

They are automatically detected if added to the `all_detectors` element in `Slither`.

## Snapshots

The snapshots are generated using [pytest-insta](https://github.com/vberlier/pytest-insta).

To update snapshots, run:

```shell
pytest tests/e2e/printers/test_printers.py --insta update
```

This will create text files in `tests/e2e/printers/snapshots/` containing the expected output of printers.




