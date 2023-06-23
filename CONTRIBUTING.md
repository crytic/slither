# Contributing to Slither

First, thanks for your interest in contributing to Slither! We welcome and appreciate all contributions, including bug reports, feature suggestions, tutorials/blog posts, and code improvements.

If you're unsure where to start, we recommend our [`good first issue`](https://github.com/crytic/slither/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) and [`help wanted`](https://github.com/crytic/slither/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) issue labels.

## Bug reports and feature suggestions

Bug reports and feature suggestions can be submitted to our issue tracker. For bug reports, attaching the contract that caused the bug will help us in debugging and resolving the issue quickly. If you find a security vulnerability, do not open an issue; email opensource@trailofbits.com instead.

## Questions

Questions can be submitted to the "Discussions" page, and you may also join our [chat room](https://empireslacking.herokuapp.com/) (in the #ethereum channel).

## Code

Slither uses the pull request contribution model. Please make an account on Github, fork this repo, and submit code contributions via pull request. For more documentation, look [here](https://guides.github.com/activities/forking/).

Some pull request guidelines:

- Work from the [`dev`](https://github.com/crytic/slither/tree/dev) branch. We performed extensive tests prior to merging anything to `master`, working from `dev` will allow us to merge your work faster.
- Minimize irrelevant changes (formatting, whitespace, etc) to code that would otherwise not be touched by this patch. Save formatting or style corrections for a separate pull request that does not make any semantic changes.
- When possible, large changes should be split up into smaller focused pull requests.
- Fill out the pull request description with a summary of what your patch does, key changes that have been made, and any further points of discussion, if applicable.
- Title your pull request with a brief description of what it's changing. "Fixes #123" is a good comment to add to the description, but makes for an unclear title on its own.

## Directory Structure

Below is a rough outline of slither's design:

```text
.
├── analyses # Provides additional info such as data dependency 
├── core # Ties everything together
├── detectors # Rules that define and identify issues 
├── slither.py # Main entry point
├── slithir # Contains the semantics of slither's intermediate representation
├── solc_parsing # Responsible for parsing the solc AST
├── tools # Miscellaneous tools built on top of slither
├── visitors # Parses expressions and converts to slithir
└── ...
```

A code walkthrough is available [here](https://www.youtube.com/watch?v=EUl3UlYSluU).

## Development Environment

Instructions for installing a development version of Slither can be found in our [wiki](https://github.com/crytic/slither/wiki/Developer-installation).

To run the unit tests, you need to clone this repository and run `make test`. Run a specific test with `make test TESTS=$test_name`. The names of tests can be obtained with `pytest tests --collect-only`.

### Linters

Several linters and security checkers are run on the PRs.

To run them locally in the root dir of the repository:

- `make lint`

> Note, this only validates but does not modify the code.

To automatically reformat the code:

- `make reformat`

We use pylint `2.13.4`, black `22.3.0`.

### Testing

Slither's test suite is divided into three categories end-to-end (`tests/e2e`), unit (`tests/unit`), and tools (`tests/tools/`).

How do I know what kind of test(s) to write?

- End-to-end: functionality that requires invoking `Slither` and inspecting some output such as printers and detectors.
- Unit: additions and modifications to objects should be accompanied by a unit test that defines the expected behavior. Aim to write functions in as pure a way as possible such that they are easier to test.
- Tools: tools built on top of Slither (`slither/tools`) but not apart of its core functionality

#### Adding detector tests

For each new detector, at least one regression tests must be present.

1. Create a folder in `tests/e2e/detectors/test_data` with the detector's argument name.
2. Create a test contract in `tests/e2e/detectors/test_data/<detector_name>/`.
3. Update `ALL_TESTS` in `tests/e2e/detectors/test_detectors.py`.
4. Run `python tests/e2e/detectors/test_detectors.py --compile` to create a zip file of the compilation artifacts.
5. `pytest tests/e2e/detectors/test_detectors.py --insta update-new`. This will generate a snapshot of the detector output in `tests/e2e/detectors/snapshots/`. If updating an existing detector, run `pytest tests/e2e/detectors/test_detectors.py --insta review` and accept or reject the updates.
6. Run `pytest tests/e2e/detectors/test_detectors.py` to ensure everything worked. Then, add and commit the files to git.

> ##### Helpful commands for detector tests
>
> - To see the tests coverage, run `pytest tests/e2e/detectors/test_detectors.py  --cov=slither/detectors --cov-branch --cov-report html`.
> - To run tests for a specific detector, run `pytest tests/e2e/detectors/test_detectors.py -k ReentrancyReadBeforeWritten`(the detector's class name is the argument).
> - To run tests for a specific version, run `pytest tests/e2e/detectors/test_detectors.py -k 0.7.6`.
> - The IDs of tests can be inspected using `pytest tests/e2e/detectors/test_detectors.py --collect-only`.

#### Adding parsing tests

1. Create a test in `tests/e2e/solc_parsing/`
2. Run `python tests/e2e/solc_parsing/test_ast_parsing.py --compile`. This will compile the artifact in `tests/e2e/solc_parsing/compile`. Add the compiled artifact to git.
3. Update `ALL_TESTS` in `tests/e2e/solc_parsing/test_ast_parsing.py`.
4. Run `python tests/e2e/solc_parsing/test_ast_parsing.py --generate`. This will generate the json artifacts in `tests/e2e/solc_parsing/expected_json`. Add the generated files to git.
5. Run `pytest tests/e2e/solc_parsing/test_ast_parsing.py` and check that everything worked.

> ##### Helpful commands for parsing tests
>
> - To see the tests coverage, run `pytest  tests/e2e/solc_parsing/test_ast_parsing.py  --cov=slither/solc_parsing --cov-branch --cov-report html`
> - To run tests for a specific test case, run `pytest tests/e2e/solc_parsing/test_ast_parsing.py -k user_defined_value_type`  (the filename is the argument).
> - To run tests for a specific version, run `pytest tests/e2e/solc_parsing/test_ast_parsing.py -k 0.8.12`.
> - To run tests for a specific compiler json format, run `pytest tests/e2e/solc_parsing/test_ast_parsing.py -k legacy` (can be legacy or compact).
> - The IDs of tests can be inspected using `pytest tests/e2e/solc_parsing/test_ast_parsing.py --collect-only`.

### Synchronization with crytic-compile

By default, `slither` follows either the latest version of crytic-compile in pip, or `crytic-compile@master` (look for dependencies in [`setup.py`](./setup.py). If crytic-compile development comes with breaking changes, the process to update `slither` is:

- Update `slither/setup.py` to point to the related crytic-compile's branch
- Create a PR in `slither` and ensure it passes the CI
- Once the development branch is merged in `crytic-compile@master`, ensure `slither` follows the `master` branch

The `slither`'s PR can either be merged while using a crytic-compile non-`master` branch, or kept open until the breaking changes are available in `crytic-compile@master`.
