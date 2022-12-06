# Contributing to Slither
First, thanks for your interest in contributing to Slither! We welcome and appreciate all contributions, including bug reports, feature suggestions, tutorials/blog posts, and code improvements.

If you're unsure where to start, we recommend our [`good first issue`](https://github.com/crytic/slither/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) and [`help wanted`](https://github.com/crytic/slither/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) issue labels.

## Bug reports and feature suggestions
Bug reports and feature suggestions can be submitted to our issue tracker. For bug reports, attaching the contract that caused the bug will help us in debugging and resolving the issue quickly. If you find a security vulnerability, do not open an issue; email opensource@trailofbits.com instead.

## Questions
Questions can be submitted to the issue tracker, but you may get a faster response if you ask in our [chat room](https://empireslacking.herokuapp.com/) (in the #ethereum channel).

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

To run the unit tests, you need to clone this repository and run `pip install ".[dev]"`.

### Linters

Several linters and security checkers are run on the PRs.

To run them locally in the root dir of the repository:

- `pylint slither tests --rcfile pyproject.toml`
- `black . --config pyproject.toml`

We use pylint `2.13.4`, black `22.3.0`.

### Detectors tests

For each new detector, at least one regression tests must be present.

- Create a test in `tests`
- Update `ALL_TEST` in `tests/test_detectors.py`
- Run `python ./tests/test_detectors.py --generate`. This will generate the json artifacts in `tests/expected_json`. Add the generated files to git.
  - If updating an existing detector, identify the respective json artifacts and then delete them, or run `python ./tests/test_detectors.py --overwrite` instead.
- Run `pytest ./tests/test_detectors.py` and check that everything worked.

To see the tests coverage, run `pytest  tests/test_detectors.py  --cov=slither/detectors --cov-branch --cov-report html`

### Parser tests
- Create a test in `tests/ast-parsing`
- Run `python ./tests/test_ast_parsing.py --compile`. This will compile the artifact in `tests/ast-parsing/compile`. Add the compiled artifact to git.
- Run `python ./tests/test_ast_parsing.py --generate`. This will generate the json artifacts in `tests/ast-parsing/expected_json`. Add the generated files to git.
- Run `pytest ./tests/test_ast_parsing.py` and check that everything worked.

To see the tests coverage, run `pytest  tests/test_ast_parsing.py  --cov=slither/solc_parsing --cov-branch --cov-report html`

### Synchronization with crytic-compile
By default, `slither` follows either the latest version of crytic-compile in pip, or `crytic-compile@master` (look for dependencies in [`setup.py`](./setup.py). If crytic-compile development comes with breaking changes, the process to update `slither` is:
- Update `slither/setup.py` to point to the related crytic-compile's branch
- Create a PR in `slither` and ensure it passes the CI
- Once the development branch is merged in `crytic-compile@master`, ensure `slither` follows the `master` branch

The `slither`'s PR can either be merged while using a crytic-compile non-`master` branch, or kept open until the breaking changes are available in `crytic-compile@master`.
