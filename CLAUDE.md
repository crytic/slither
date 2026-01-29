# Coding Standards

## Code Quality
1. ≤ 50 code lines / function
2. Cyclomatic complexity ≤ 8
3. ≤ 5 positional params, ≤ 12 branches, ≤ 6 returns
4. 100‑char line length
5. Ban relative (`..`) imports
6. Google‑style docstrings on non-trivial public APIs
7. Follow project's existing test conventions; for new projects, use language defaults (Python: `tests/` directory, Node/TS: colocated `*.test.ts`)
8. No scheduled CI without code changes - activity without progress is theater
9. All code must pass type checking—no `type: ignore` without justification (Python: `ty --strict`, TypeScript: `tsc --noEmit`)

## Philosophy
- **No speculative features** - Don't add "might be useful" functionality
- **No premature abstraction** - Don't create utilities until you've written the same code three times
- **Justify new dependencies** - Each dependency is attack surface and maintenance burden
- **No unnecessary configuration** - Don't add flags unless users actively need them
- **No phantom features** - Don't document or validate features that aren't implemented
- **No hardcoded paths** - Use environment variables or config files, not `/Users/yourname/...`

## CLI Tools
| tool | replaces | usage |
|------|----------|--------|
| `rg` (ripgrep) | grep | `rg "pattern"` - 10x faster regex search |
| `fd` | find | `fd "*.py"` - fast file finder (`fdfind` on Debian/Ubuntu) |
| `ast-grep` | - | `ast-grep --pattern '$FUNC($$$)' --lang py` - AST-based code search |
| `shellcheck` | - | `shellcheck script.sh` - shell script linter |
| `shfmt` | - | `shfmt -i 2 -w script.sh` - shell formatter |
| `actionlint` | - | `actionlint .github/workflows/` - GitHub Actions linter |
| `zizmor` | - | `zizmor .github/workflows/` - Actions security audit |

```bash
# ast-grep structural search (prefer over grep for code patterns)
ast-grep --pattern 'print($$$)' --lang py              # Find function calls
ast-grep --pattern 'class $NAME: $$$' --lang py        # Find classes
ast-grep --pattern 'async def $F($$$): $$$' --lang py  # Find async functions
# $NAME = identifier, $$$ = any code. Languages: py, js, ts, rust, go
```

## Workflow

When making changes:
1. Always run linters and type checker before committing
2. Run relevant tests (not full suite) after changes
3. Use `git diff` to verify changes before committing

General rules:
- Never commit changes that break any rule above—refactor instead
- Never push changes to GitHub until asked explicitly to do so
- If asked to write PRs or Issues, don't be hyperbolic in your writeups

### GitHub Actions
Pin actions to SHA hashes with version comments:
```yaml
- uses: actions/checkout@<full-sha>  # vX.Y.Z
  with:
    persist-credentials: false
```

### Dependabot Cooldowns
Configure Dependabot with 7-day cooldowns to protect against supply chain attacks:
```yaml
# .github/dependabot.yml - repeat for: pip, npm, github-actions
- package-ecosystem: <ecosystem>
  directory: /
  schedule:
      interval: weekly
  cooldown:
      default-days: 7
  groups:
      all:
          patterns: ["*"]
```

## Version Verification
When adding or updating dependencies, CI actions, or tool versions:
1. **Always web search** for the current stable version before specifying any version number
2. Training data versions are stale—never assume a version from memory is current
3. Check the official source (PyPI, npm, GitHub releases) for latest stable
4. Exception: Only skip web search if user explicitly provides the version to use

## Python

**Runtime:** 3.13 with `uv venv`

| purpose          | tool                           |
|------------------|--------------------------------|
| deps & venv      | `uv`                           |
| lint & format    | `ruff check` · `ruff format`   |
| static types     | `ty --strict`                  |
| tests            | `pytest -q`                    |

Always use `uv` instead of pip - it's faster and handles venvs automatically.
Build with `hatchling` - simpler than setuptools, just `[build-system]` in pyproject.toml.
Lint with `ruff` only - replaces black/pylint/flake8, use `extend-exclude` not `exclude`.
Use official actions - `astral-sh/ruff-action@<sha>  # vX.Y.Z`
Linting versions - Keep flexible (`ruff>=0.12.0,<1.0`) - newer versions find more bugs, can't break working code.
Remove pip fallbacks - no `pip || uv` patterns, pick one tool and commit.
Test modernizations - always verify: `uv build`, `uv tool install dist/*.whl`, `uv tool install -e .`
Update all references - every README, Makefile, CI config must be updated.
Let tools auto-detect - Don't specify versions in CI that tools can read from pyproject.toml

Type checking with `ty`:
- **New projects**: `ty --strict` is mandatory—no untyped code accepted
- **Existing projects**: Add type checking incrementally when modifying code
- Run `uv run ty check` before committing Python changes
- Add `py.typed` marker file to indicate typed packages

### Commands
```bash
uv run ruff check --fix
uv run ty check
pytest -q

# Find outdated Python tooling
rg "pip|setup.py|black|pylint" -g "*.md" -g "*.yml"
```

### Security
- Use `uv` lockfiles (`uv.lock`) - ensures reproducible, verified installs
- Run `pip-audit` or `safety check` before deploying
- Pin exact versions in production (`==` not `>=`)
- Verify package hashes: `uv pip install --require-hashes`

## Node/TypeScript

**Runtime:** Node 22 LTS

| purpose      | tool                           |
|--------------|--------------------------------|
| lint         | `oxlint`                       |
| format       | `oxfmt`                        |
| test         | `vitest`                       |
| types        | `tsc --noEmit`                 |

Use the [Oxc toolchain](https://oxc.rs/) (Rust-powered, 50-100x faster than ESLint/Prettier).
Use [Vitest](https://vitest.dev/) for testing - native ESM/TypeScript, drop-in Jest replacement.

### Commands
```bash
oxlint .
oxfmt --write .
vitest run
tsc --noEmit
```

### Security
```bash
# MANDATORY before any install
pnpm config set minimumReleaseAge 1440  # 24-hour delay
pnpm config set ignore-scripts true     # Block postinstall attacks
# For packages that need scripts (review first!)
pnpm install --ignore-scripts && pnpm rebuild <package-name>
```

- Never install packages < 24 hours old
- Never enable postinstall scripts without review
- Audit first: `pnpm audit --audit-level=moderate`
- Pin exact versions (no `^` or `~`) in production
- Review package.json changes in PRs for suspicious scripts

## Bash
All bash scripts must start with strict mode:
```bash
#!/bin/bash
set -euo pipefail
```
This makes many subtle bugs impossible by:
- Exiting on any command failure (`-e`)
- Exiting on undefined variables (`-u`)
- Failing pipelines if any command fails (`-o pipefail`)

Lint shell scripts before committing:
```bash
shellcheck script.sh
shfmt -d script.sh  # Check formatting (-w to fix)
```
