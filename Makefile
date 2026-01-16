SHELL := /bin/bash

PY_MODULE := slither
TEST_MODULE := tests
SCRIPT_MODULE := scripts

# Optionally overridden by the user in the `test` target.
TESTS :=

# If the user selects a specific test pattern to run, set `pytest` to fail fast
# and only run tests that match the pattern.
ifneq ($(TESTS),)
	TEST_ARGS := -x -k $(TESTS)
else
	TEST_ARGS := -n auto
endif

.PHONY: help
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Setup:"
	@echo "  dev        Install dependencies and pre-commit hooks"
	@echo ""
	@echo "Development:"
	@echo "  lint       Run all linters (ruff, yamllint, actionlint, zizmor)"
	@echo "  reformat   Auto-fix lint issues and format code"
	@echo "  test       Run test suite (use TESTS=pattern to filter)"
	@echo "  check      Run lint + test"
	@echo "  run        Run slither (use ARGS='...' to pass arguments)"
	@echo ""
	@echo "Build:"
	@echo "  doc        Generate documentation"
	@echo "  package    Build distribution package"
	@echo "  clean      Remove build artifacts and caches"

.PHONY: dev
dev:
	uv sync --group dev
	prek install

.PHONY: run
run:
	uv run slither $(ARGS)

.PHONY: lint
lint:
	uv run ruff check $(PY_MODULE) $(TEST_MODULE) $(SCRIPT_MODULE)
	uv run yamllint -c .yamllint .github/
	actionlint
	zizmor .github/workflows/

.PHONY: reformat
reformat:
	uv run ruff check --fix $(PY_MODULE) $(TEST_MODULE) $(SCRIPT_MODULE)
	uv run ruff format $(PY_MODULE) $(TEST_MODULE) $(SCRIPT_MODULE)

.PHONY: test tests
test tests:
	uv run pytest --cov=$(PY_MODULE) $(T) $(TEST_ARGS)
	uv run coverage report -m

.PHONY: check
check: lint test

.PHONY: doc
doc:
	PDOC_ALLOW_EXEC=1 uv run pdoc -o html slither '!slither.tools'

.PHONY: package
package:
	uv build

.PHONY: clean
clean:
	rm -rf .venv/ build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/ html/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
