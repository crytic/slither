# Rounding Analysis

A forward data-flow analysis that tracks rounding direction through Solidity
arithmetic. It tags every variable with a direction (UP, DOWN, NEUTRAL, UNKNOWN),
propagates tags through operations following algebraic rules, and reports
conflicts where UP and DOWN mix in the same expression.

Based on the rules from [roundme](https://github.com/crytic/roundme).

## Quick Start

```bash
# Run as a data-flow analysis
slither project/ --analyze rounding
```

The analysis runs on every implemented function in every contract, prints
annotated source with per-variable tags (via Rich), and reports
inconsistencies. Use `--json -` to get structured output instead.

### CLI Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `--rounding-trace UP\|DOWN\|UNKNOWN` | off | Show tag provenance traces for this direction |
| `--rounding-safe-libs [path]` | off | Use known library tags (`__builtin__` or a JSON file) |
| `--rounding-show-all` | off | Show annotations for all variables including params |

## Tags

```
UP       — value was computed rounding up (ceiling)
DOWN     — value was computed rounding down (floor / truncation)
NEUTRAL  — no rounding information (default for parameters and state variables)
UNKNOWN  — direction unclear or conflicting (always triggers an inconsistency)
```

Variables can carry multiple tags simultaneously when different branches
produce different directions. For example, a function with
`if (roundUp) { divUp() } else { divDown() }` produces `{DOWN, UP}` on the
merged result. A multi-tag set is not itself an inconsistency -- it means the
rounding direction depends on the execution path.

## Arithmetic Rules

| Operation | Rule | Example |
|-----------|------|---------|
| `A + B` | `combine(tag(A), tag(B))` | `DOWN + NEUTRAL = DOWN` |
| `A - B` | `combine(tag(A), invert(tag(B)))` | `NEUTRAL - DOWN = UP` |
| `A * B` | `combine(tag(A), tag(B))` | `UP * NEUTRAL = UP` |
| `A / B` | `combine(tag(A), invert(tag(B)))` with floor bias | `NEUTRAL / NEUTRAL = DOWN` |

**combine**: NEUTRAL yields to the other tag. Same + Same = Same.
UP + DOWN = UNKNOWN (conflict).

**invert**: UP becomes DOWN, DOWN becomes UP, NEUTRAL and UNKNOWN stay.

**Floor bias** (division only): when either operand is NEUTRAL, the result
defaults to DOWN because Solidity's integer truncation dominates a single
operand's signal. When both operands carry non-NEUTRAL tags (e.g., both DOWN),
the division handler flags an inconsistency.

**Ceiling pattern**: the handler detects `(a + b - 1) / b` by walking the
producer chain. If the dividend was produced by `X - 1` where `X = a + b` and
one addend matches the divisor, the result is tagged UP.

## Tag Sources (Priority Order)

When analyzing a function call, the interprocedural handler resolves the
callee's return tag using these sources, highest priority first:

1. **Inline annotation** -- `//@round funcName=DOWN` comment on the call site
2. **Name inference** -- function name contains `down`/`floor` (DOWN) or
   `up`/`ceil` (UP). Names containing both are ambiguous and fall through.
3. **Known library tags** -- lookup in a `(contract, function)` dict.
   Built-in: `FullMath.mulDiv` = DOWN, `FullMath.mulDivRoundingUp` = UP.
   Extensible via JSON file.
4. **Body analysis** -- full interprocedural analysis of the callee's CFG,
   binding caller argument tags to callee parameters.

## How It Runs

```
RoundingCLI.run(slither)
  for each contract, for each function:
    annotate.analyze_function(function)
      1. Create RoundingAnalysis (with handler registry)
      2. Create Engine.new(analysis, function)
         → initializes worklist with BOTTOM state for each CFG node
      3. engine.run_analysis()
         → forward worklist fixpoint:
            pop node → transfer_function(node, pre_state, operation)
              - promote BOTTOM → STATE
              - initialize entry state (params, state vars → NEUTRAL)
              - dispatch operation to handler via registry
            set post = pre
            propagate pre to successors via join (set union of tags)
            add changed successors to worklist
      4. engine.result() → Dict[Node, AnalysisState]
      5. Build AnnotatedFunction from node results
      6. Extract variable traces from node results
    RoundingCLI.display() / .serialize() / .summarize()
      display()   → Rich console output + trace section
      serialize() → full JSON for --json output
      summarize() → lightweight summaries for MCP caching
```

## Interprocedural Analysis

When a call is encountered (`InternalCall`, `HighLevelCall`, `LibraryCall`):

1. Try tag sources 1-3 (annotation, name, known lib). If resolved, apply the
   tag directly to the call's lvalue and build a trace node.
2. If unresolved, perform body analysis:
   - Push the callee onto a call stack (recursion guard -- recursive calls
     return UNKNOWN).
   - Create a fresh domain for the callee.
   - Bind caller argument tags to callee parameters (matching SSA base names).
   - Walk the callee's CFG, dispatching every operation through the same
     handler registry.
   - Extract return-value tags from `Return` operations.
   - Pop the callee from the call stack.
3. For tuple returns, extract per-index tags and apply them to the
   corresponding `Unpack` lvalues.

## Branch Handling

At conditional nodes (`IF`, `IFLOOP`), the engine forks the domain into true
and false branches. Each branch is propagated independently. When branches
rejoin at a merge point, `RoundingDomain.join()` computes the **set union** of
tag sets per variable, stripping NEUTRAL when a non-NEUTRAL tag exists. This
means a variable can carry `{DOWN, UP}` after a merge -- the direction depends
on which branch executed.

## Inline Annotations

Two mechanisms for developer-supplied rounding expectations:

### Source comments (`//@round`)

```solidity
uint result = someLib.compute(x, y); //@round compute=DOWN
```

Parsed by regex. Supports comma-separated entries:
`//@round f1=UP, f2=DOWN`. These override all other tag sources for the
annotated call.

### Variable name suffixes

Variables ending in `_UP`, `_DOWN`, or `_NEUTRAL` are expected to carry that
tag. Mismatches are reported as `annotation_mismatches` (separate from
inconsistencies). Checked at assignment, return, and call sites.

## Known Library Tags

A dictionary mapping `(contract_name, function_name)` to a `RoundingTag`.

Built-in defaults:
```
FullMath.mulDiv         → DOWN
FullMath.mulDivRoundingUp → UP
```

Extend with a JSON file:
```json
{
  "MyLib.safeDiv": "DOWN",
  "MyLib.ceilDiv": "UP"
}
```

Pass via `--rounding-safe-libs` (built-ins only) or
`--rounding-safe-libs path/to/tags.json` (user file merged over built-ins).

## Output Formats

`RoundingCLI` exposes three output methods, each serving a different consumer:

### `display()` — Rich console (default)

Prints annotated source with inline tags, return summaries, inconsistencies,
and optional provenance traces (`--rounding-trace`). For human consumption.

### `serialize()` → `List[RoundingResult]` — CLI `--json`

Full serialization including annotated source lines, per-line annotations,
complete trace trees (`TraceNodeDict`, recursive up to depth 10), and findings
with line/variable references. Used by `--json -` for downstream tooling.

### `summarize()` → `List[RoundingSummary]` — MCP

Lightweight summaries for slither-mcp's `ProjectFacts` cache. Drops source
text, line annotations, and trace trees. Keeps only:

- `variable_tags` — exit-state tags per variable (NEUTRAL-only vars omitted)
- `return_tags` — function return directions
- `inconsistencies` / `annotation_mismatches` — message strings only

MCP caches these summaries cheaply, then calls `get_traces(function_name,
variable_name)` on demand when a user drills into a specific variable's
provenance chain.

## Tests

```bash
pytest tests/e2e/data_flow/rounding/ -v
```
