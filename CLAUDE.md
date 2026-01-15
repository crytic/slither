# Slither Coding Standards

## Runtime
| lang   | version | manager |
|--------|---------|---------|
| Python | ≥3.9    | uv      |

## Required tooling
| purpose          | tool     |
|------------------|----------|
| deps & venv      | `uv`     |
| lint & format    | `ruff`   |
| tests            | `pytest` |

## Python guidelines
- Always use `uv` instead of pip
- Build with `hatchling` (`[build-system]` in pyproject.toml)
- Use `astral-sh/ruff-action@v3` or newer in CI
- Let tools auto-detect versions from pyproject.toml
- Verify builds: `uv build`, `uv tool install dist/*.whl`, `uv tool install -e .`

## Version Verification
When adding or updating dependencies, CI actions, or tool versions:
1. **Always web search** for the current stable version before specifying any version number
2. Training data versions are stale—never assume a version from memory is current
3. Check the official source (PyPI, GitHub releases) for latest stable
4. Exception: Only skip web search if user explicitly provides the version to use

## Hard rules
1. ≤ 80 code lines / function
2. Cyclomatic complexity ≤ 8
3. ≤ 5 positional params, ≤ 12 branches, ≤ 6 returns
4. 100‑char line length
5. Ban relative ("..") imports
6. Tests in `/tests/` mirroring package structure (not beside code)
7. No scheduled CI without code changes

## Bash strict mode
All bash scripts must start with:
```bash
#!/bin/bash
set -euo pipefail
IFS=$'\n\t'
```

## Common commands
```bash
make dev                    # Create venv and install deps
make lint                   # Run ruff check
make reformat               # Run ruff format
make test                   # Run all tests
make test TESTS=unit        # Run specific test directory
pytest tests/unit/ -q       # Fast unit tests only
uv run ruff check --fix .   # Auto-fix lint issues
```

> Never commit changes that break any rule above—refactor instead.
> Never push to GitHub until asked explicitly.
> Don't be hyperbolic in PR/Issue writeups.
