# Contributing to Slither

First, thanks for your interest in contributing to Slither! We welcome and appreciate all contributions, including bug reports, feature suggestions, tutorials/blog posts, and code improvements.

If you're unsure where to start, we recommend our [`good first issue`](https://github.com/crytic/slither/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) and [`help wanted`](https://github.com/crytic/slither/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) issue labels.

## Bug reports and feature suggestions

Bug reports and feature suggestions can be submitted to our issue tracker. For bug reports, attaching the contract that caused the bug will help us in debugging and resolving the issue quickly. If you find a security vulnerability, do not open an issue; email <opensource@trailofbits.com> instead.

## Questions

Questions can be submitted to the "Discussions" page, and you may also join our [chat room](https://empireslacking.herokuapp.com/) (in the #ethereum channel).

## Code

Submit contributions via pull request.

- Minimize irrelevant changes (formatting, whitespace). Save style fixes for separate PRs.
- Split large changes into smaller focused PRs.
- PR description: summarize changes. For bug fixes, explain root cause.
- PR title: describe what it's changing (not just "Fixes #123").
- Commit messages: ≤72 char subject, prefix with `fix:`, `feat:`, `docs:`, `test:`, `refactor:`.

## Directory Structure

See the Architecture section in [CLAUDE.md](CLAUDE.md) for directory layout. A code walkthrough is available [here](https://www.youtube.com/watch?v=EUl3UlYSluU).

## Development Environment

Instructions for installing a development version of Slither can be found in our [wiki](https://github.com/crytic/slither/wiki/Developer-installation).

For development setup, we use [uv](https://github.com/astral-sh/uv):

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup development environment
make dev  # Creates venv and installs all dependencies
```

Run `make test` for all tests, or `make test TESTS=$name` for specific tests. List test names with `pytest tests --collect-only`.

### Linters

Run `make lint` to check and `make reformat` to auto-fix. We use ruff for Python and yamllint for YAML.

#### Pre-commit Hooks (Recommended)

We use [prek](https://github.com/j178/prek), a fast Rust-based pre-commit runner:

```bash
prek install               # One-time setup
prek run --all-files       # Run manually
prek auto-update --cooldown-days 7  # Update hook versions
```

### Testing

Slither's test suite has three categories:

- **End-to-end** (`tests/e2e`): Invoke Slither and check output (printers, detectors).
- **Unit** (`tests/unit`): Test individual objects and functions.
- **Tools** (`tests/tools`): Tests for `slither/tools`.

#### Adding detector tests

For each new detector, at least one regression tests must be present.

1. Create a folder in `tests/e2e/detectors/test_data` with the detector's argument name.
2. Create a test contract in `tests/e2e/detectors/test_data/<detector_name>/`.
3. Update `ALL_TESTS` in `tests/e2e/detectors/test_detectors.py`.
4. Run `python tests/e2e/detectors/test_detectors.py --compile` to create a ZIP file of the compilation artifacts.
5. `pytest tests/e2e/detectors/test_detectors.py --insta update-new`. This will generate a snapshot of the detector output in `tests/e2e/detectors/snapshots/`. If updating an existing detector, run `pytest tests/e2e/detectors/test_detectors.py --insta review` and accept or reject the updates.
6. Run `pytest tests/e2e/detectors/test_detectors.py` to ensure everything worked. Then, add and commit the files to git.

> **Tip:** Filter with `-k ReentrancyReadBeforeWritten` (class) or `-k 0.7.6` (version). Add `--cov=slither/detectors --cov-report=html` for coverage.

#### Adding parsing tests

1. Create a test in `tests/e2e/solc_parsing/`
2. Update `ALL_TESTS` in `tests/e2e/solc_parsing/test_ast_parsing.py`.
3. Run `python tests/e2e/solc_parsing/test_ast_parsing.py --compile`. This will compile the artifact in `tests/e2e/solc_parsing/compile`. Add the compiled artifact to git.
4. Run `python tests/e2e/solc_parsing/test_ast_parsing.py --generate`. This will generate the json artifacts in `tests/e2e/solc_parsing/expected_json`. Add the generated files to git.
5. Run `pytest tests/e2e/solc_parsing/test_ast_parsing.py` and check that everything worked.

> **Tip:** Filter with `-k user_defined_value_type` (filename), `-k 0.8.12` (version), or `-k legacy` (format). Add `--cov=slither/solc_parsing --cov-report=html` for coverage.

### Coordinating Changes with crytic-compile

Slither depends on [crytic-compile](https://github.com/crytic/crytic-compile) for compilation. When making changes that require updates to both repos:

1. Create a branch in crytic-compile with your changes
2. Update slither's `pyproject.toml` to point to that branch:
   ```
   "crytic-compile @ git+https://github.com/crytic/crytic-compile.git@your-branch"
   ```
3. Create a PR in slither and verify CI passes
4. After crytic-compile merges, update slither to use the released version
