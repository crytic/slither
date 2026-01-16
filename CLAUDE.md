# Slither

Static analyzer for Solidity smart contracts. Detects vulnerabilities, prints contract information, and provides an intermediate representation (SlithIR) for analysis.

## Architecture

```
slither/
├── detectors/     # Security checks (subclass AbstractDetector)
├── printers/      # Output formatters (subclass AbstractPrinter)
├── slithir/       # Intermediate representation for analysis
├── solc_parsing/  # Solidity AST parsing
├── tools/         # CLI tools (slither-read-storage, slither-mutate, etc.)
└── core/          # Core classes: SlitherCore, Contract, Function
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed architecture and how to add detectors.

## Development

| tool    | purpose       |
|---------|---------------|
| `uv`    | deps & venv   |
| `ruff`  | lint & format |
| `pytest`| tests         |

```bash
make dev                    # Setup dev environment
make lint                   # Run ruff check
make reformat               # Run ruff format
make test                   # Run all tests
pytest tests/unit/ -q       # Fast unit tests only
```

### Navigating the codebase

Use `rg` for text search and `ast-grep` for structural patterns:

```bash
# Find class definition
ast-grep --pattern 'class Contract($_): $$$' --lang py slither

# Find all detector implementations
ast-grep --pattern 'class $NAME(AbstractDetector): $$$' --lang py slither/detectors

# Find method usages
rg "\.is_interface" slither

# Find function signatures
ast-grep --pattern 'def _detect($$$)' --lang py slither/detectors

# Trace imports
rg "^from slither\.core" slither
```

## Code Standards

### Philosophy
- **No speculative features** - Don't add "might be useful" functionality
- **No premature abstraction** - Don't create utilities until you've written the same code three times
- **Clarity over cleverness** - Prefer explicit, readable code over dense one-liners
- **Justify new dependencies** - Each dependency is maintenance burden and complexity
- **Structured output first** - New commands must support `--json`. Human-readable is secondary.
- **Atomic operations** - Don't bundle decision logic; separate analyze → suggest → apply for composability.

### Code quality
- **Comments** - Code should be self-documenting. No commented-out code (delete it). No comments that repeat what code does.
- **Errors** - Fail fast with clear, actionable messages. Include context: what failed, which file/contract, suggested fix. Never swallow exceptions.
- **When uncertain** - State your assumption and proceed for small decisions. Ask before changes with significant consequences.

### Hard limits
1. ≤80 lines/function, cyclomatic complexity ≤8
2. ≤5 positional params, ≤12 branches, ≤6 returns
3. 100-char line length
4. No relative (`..`) imports
5. Tests in `/tests/` mirroring package structure

Bash scripts must use strict mode:
```bash
#!/bin/bash
set -euo pipefail
```

## Working on Code

### Incremental improvement
When modifying a file, improve what you touch. Don't refactor unrelated code—keep PRs focused.

Modernization targets:
- Type hints on function signatures (aspiration: `ty --strict`)
- `pathlib.Path` over `os.path` string manipulation
- f-strings over `.format()` or `%` formatting
- Context managers (`with`) for file/resource handling
- Early returns to reduce nesting
- Fix lint issues you encounter

### Git conventions
- Commit messages: imperative mood, ≤72 char subject (e.g., "Fix reentrancy false positive")
- One logical change per commit
- Prefix: `fix:`, `feat:`, `refactor:`, `test:`, `docs:` as appropriate

## Testing

- **Mock boundaries, not logic** - Only mock slow things (network, filesystem), non-deterministic things (time), or external services. Don't mock the code you're testing.
- **Verify tests catch failures** - Temporarily break code to verify the test fails, then fix it.

### Slither-specific
- Test detectors across Solidity 0.4.x–0.8.x
- Update snapshots: `tests/e2e/detectors/snapshots/`
- Use `compile_force_framework="solc"` when crytic-compile behavior changes

## Slither Internals

### APIs
- Use `contract.is_interface` not `contract.name.startswith("I")`
- Use `source_mapping.content` for source code access (handles byte/char offsets)
- Use `is` / `is not` for enum comparisons (`NodeType.X`, not `== NodeType.X`)
- CLI features should have Python API equivalents in the `Slither` class

### Traversal patterns
- **Use `_declared` suffix** - `functions_declared`, `state_variables_declared` avoid processing inherited items multiple times
- Filter by `function.contract_declarer == contract` when iterating `contract.functions`
- `high_level_calls` returns `List[Tuple[Contract, Call]]` - don't forget tuple unpacking
- Standard detector loop: contracts → `functions_and_modifiers_declared` → nodes → irs

### Type handling
- Expand `isinstance()` checks rather than removing assertions
- Add type guards before accessing type-specific attributes in AST visitors
- Check local scope before broader scope when resolving identifiers

### SlithIR and SSA
- **Use `node.irs`** for most detectors—simpler, sufficient for most analyses
- **Use `node.irs_ssa`** only when you need precise data flow (tracking reassignments, taint analysis)
- SSA variables have `.index` (e.g., `x_0`, `x_1`) and `.non_ssa_version` to get the original
- `Phi` operations merge SSA versions at control flow joins (if/else, loops)
- **Data dependency**: Use `is_dependent(var, source, context)` from `slither.analyses.data_dependency`

### Detector quality
Minimize false positives over catching edge cases. Noisy detectors get disabled. Output must be actionable.

### Docstrings
Detectors use class attributes, not Google-style docstrings:
- `WIKI_TITLE`, `WIKI_DESCRIPTION`, `WIKI_EXPLOIT_SCENARIO`, `WIKI_RECOMMENDATION`
- Must be thorough—agents use these to decide which detectors apply
- `VULNERABLE_SOLC_VERSIONS` restricts detector to specific compiler versions
- Use `make_solc_versions(minor, patch_min, patch_max)` helper for version lists

## Notes

**Version verification**: When adding dependencies or CI actions, web search for current stable versions. Training data is stale—never assume a version from memory is current.

---

> Don't push until asked. Don't be hyperbolic in PR writeups.
