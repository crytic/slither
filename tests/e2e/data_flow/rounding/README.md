# Rounding Direction Analysis

Data-flow analysis tracking rounding error propagation in Solidity. Based on [roundme](https://github.com/crytic/roundme).

## Tags

- `UP` - Value rounded up (ceiling)
- `DOWN` - Value rounded down (floor)
- `NEUTRAL` - No rounding info (constants, parameters)
- `UNKNOWN` - Conflicting or unclear direction

## State

Each variable maps to a **TagSet** (set of possible tags). A variable can have multiple tags after control flow merges, e.g., `{DOWN, UP}`.

## Join

When branches merge, tags are unioned. NEUTRAL is absorbed by other tags:
```
{UP} | {DOWN} = {DOWN, UP}
{UP} | {NEUTRAL} = {UP}
```

## Binary Rules

From roundme:

- **Addition** `A + B`: `rounding(A), rounding(B)` - must agree
- **Subtraction** `A - B`: `rounding(A), !rounding(B)` - B is inverted
- **Multiplication** `A * B`: `rounding(A), rounding(B)` - must agree
- **Division** `A / B`: `rounding(A), !rounding(B)` - B is inverted, defaults to DOWN

Ceiling pattern `(a + b - 1) / b` is detected as UP.

## Name Inference

- `divDown`, `mulDown`, `floor` → DOWN
- `divUp`, `mulUp`, `ceil` → UP
- Contains both → falls back to body analysis

## Interprocedural

1. Try name inference first
2. If neutral/ambiguous, analyze function body
3. Map argument tags to parameters, extract return tags

## Tracing

`--trace DOWN` shows provenance chain:
```
result (line 42):
  └── helper() returns DOWN
    └── divDown() → DOWN
```

## Usage

```bash
uv run python -m slither.analyses.data_flow.analyses.rounding.run_analysis \
  <path> -c <Contract> --function <func> --trace DOWN
```

## Tests

```bash
uv run pytest tests/e2e/data_flow/rounding/ -v
```
