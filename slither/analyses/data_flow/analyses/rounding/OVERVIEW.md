# Rounding Analysis

A forward data-flow analysis that tracks rounding direction through Solidity
arithmetic. It tags every variable with a direction (UP, DOWN, NEUTRAL, UNKNOWN),
propagates tags through operations following algebraic rules, and reports
conflicts where UP and DOWN mix in the same expression.

Based on the rules from [roundme](https://github.com/crytic/roundme).

## Quick Start

```bash
# Run as a Slither detector
slither project/ --detect rounding-inconsistency
```

The detector analyzes every implemented function in every contract, prints
annotated source with per-variable tags, and reports inconsistencies as
findings.

### Configuration

Edit the class-level flags in
`slither/detectors/rounding_df/rounding_inconsistency.py`:

| Flag | Default | Purpose |
|------|---------|---------|
| `TRACE_TAG` | `None` | Set to `"UP"`, `"DOWN"`, or `"UNKNOWN"` to show provenance chains |
| `EXPLAIN` | `False` | Use an LM (via DSPy) to explain trace chains |
| `EXPLAIN_MODEL` | `"anthropic/claude-sonnet-4-5-20250929"` | LM model identifier |
| `SAFE_LIBS` | `None` | `"__builtin__"` or path to a JSON file of known library tags |
| `SHOW_ALL` | `False` | Show NEUTRAL parameter annotations at entry points |
| `TARGET_FUNCTIONS` | `None` | List of function names to analyze, e.g. `["onSwap", "withdraw"]` |

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
RoundingInconsistency._detect()
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
    Display annotated source (Rich console)
    Collect RoundingFindings → Slither Output objects
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

Pass via `SAFE_LIBS = "__builtin__"` (built-ins only) or
`SAFE_LIBS = "path/to/tags.json"` (user file merged over built-ins).

## LM Trace Explanation

When `EXPLAIN = True` and `TRACE_TAG` is set, the analysis uses DSPy to have
an LM explain each provenance chain.

```
configure_dspy(model)              # reads .env for API key
TraceExplainer()                   # creates dspy.Predict(AnalyzeRoundingTrace)
for each traced variable:
    split_trace_paths(trace, tag)  # tree → list of linear root-to-leaf paths
    for each path:
        serialize_trace_path(path)       # path → text for LM
        extract_source_for_path(path)    # Solidity source per function
        explainer(...)                   # DSPy call → TraceAnalysis (Pydantic)
        render trace steps               # Rich console output
```

Each `TraceStep` in the output contains:
- `condition` -- branch condition to reach this step
- `inputs` -- what values flow in
- `operation` -- the arithmetic producing the direction
- `next_call` -- which function is called next

Requires `pip install slither-analyzer[explain]` and an
`ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`) in `.env` or the environment.

## Tests

```bash
pytest tests/e2e/data_flow/rounding/ -v
```
