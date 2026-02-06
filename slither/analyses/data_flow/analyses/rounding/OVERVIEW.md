# Rounding Analysis - Overview

I kept working on the rounding analysis. 

**How it works:**
1. Tags variables with rounding directions (UP, DOWN, NEUTRAL, UNKNOWN)
2. Propagates tags through arithmetic operations following mathematical rules
3. Analyzes function calls to track tags across call boundaries
4. Reports conflicts where UP and DOWN mix incorrectly

**Core Rules (from [roundme](https://github.com/crytic/roundme)):**

| Operation | Rule |
|-----------|------|
| A + B | Both operands propagate directly |
| A - B | Subtrahend's direction inverts |
| A * B | Both operands propagate directly |
| A / B | Denominator's direction inverts; defaults to DOWN |

**Tag Sources:**
- Function names containing "up/ceil" → UP, "down/floor" → DOWN
- Division operations → DOWN (as disucessed)
- Interprocedural analysis when names are ambiguous

**Key Features:**
- `--trace UP/DOWN` flag shows provenance chains for debugging
- Detects ceiling division pattern `(a + b - 1) / b`
- Handles branching (if/else) by taking union of possible tags

## LM-Powered Trace Explanation (`--explain`)

The `--explain` flag uses DSPy to have an LM identify the concrete conditions that lead to each rounding direction in a trace chain.

**How DSPy plugs in:**

```
CLI (--explain --trace DOWN)
  → configure_dspy()              # sets up LM (reads .env for API key)
  → TraceExplainer()              # creates dspy.Predict(AnalyzeRoundingTrace)
  → for each traced variable:
      → split_trace_paths()       # splits tree into linear root-to-leaf paths
      → for each path:
          → serialize_trace_path()    # path → string for LM
          → extract_source_for_path() # looks up Solidity source per function
          → explainer(...)            # DSPy calls the LM, returns typed output
          → _render_trace_steps()     # displays structured result
```

**Architecture (`explain/` module):**

| File | Role |
|------|------|
| `signature.py` | DSPy Signature + Pydantic models defining the LM contract |
| `explainer.py` | `TraceExplainer` module, path splitting, source extraction |
| `configuration.py` | LM setup, `.env` loading, API key validation |

**The Signature** (`AnalyzeRoundingTrace`) is the core — it defines inputs (trace chain, traced tag, Solidity source, contract context) and a typed output (`TraceAnalysis` containing a list of `TraceStep` objects). DSPy reads this to build the prompt, call the LM, and parse the response into Pydantic objects.

**Each `TraceStep`** bundles everything for one function in the chain:
- `condition` — branch condition to reach this step (e.g., `request.tokenIn == _mainToken`)
- `inputs` — what values flow in and where from
- `operation` — the arithmetic producing the rounding direction
- `next_call` — which function is called next

**Path splitting** is key: the trace is a tree (multiple branches can lead to DOWN), so we split into linear paths before calling the LM. Each path gets its own LM call, keeping the output focused.

**Why DSPy over raw API calls:**
- Signature = prompt — define structure, DSPy handles serialization and parsing
- Pydantic output = typed, validated response (no manual JSON parsing)
- Future: plug in `BootstrapFewShot` to optimize prompts with labeled examples

**Usage:**
```bash
# Requires ANTHROPIC_API_KEY in .env or environment
python -m slither.analyses.data_flow.analyses.rounding.run_analysis . \
  -c LinearPool.sol --function onSwap --trace DOWN --explain
```
