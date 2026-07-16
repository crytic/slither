# Stage 5: Abstract Nonlinear Transfer and Bounded Refinement

## Outcome

Operation-level interval analysis is abstract-first and solver-optional. Integer binary operations
derive a conservative interval during transfer. A tracked operation result, including a sound type
top, is returned as `ABSTRACT` without opening a query session unless a caller explicitly requests
refinement.

An unconstrained checked `uint256 x * y` now returns tagged abstract
`[0, MAX_UINT256]` in about 0.03 ms with zero solver sessions. A branch-bounded `x * 2`, where
`x=[10,99]`, returns `[20,198]` with zero solver sessions. The Stage 4 fixed loop still completes in
39 iterations, opens zero widening sessions, and returns `sum_2=[0,45]`.

Stage 1 fact identity, Stage 2 function/session ownership, Stage 3 state joins, and Stage 4 loop
generation semantics are unchanged. Stage 5 does not alter worklist topology, node revisit policy,
join, widening, property behavior, or public analysis entry points.

## Abstract transfer design

`abstract_transfer.py` defines:

- `AbstractTransferKind.EXACT`, `INTERVAL`, and `TOP`;
- `AbstractTransferResult`, containing the interval, precision kind, wrap possibility, and whether
  the transformer supports the case; and
- `transfer_binary_interval`, the backend-independent transfer entry point.

Every returned interval is intersected with, or replaced by, the destination integer type range.
Unsupported cases return type top with `supported=False`; they do not guess a narrower range.

### Addition and subtraction

For operand intervals `A=[a_l,a_u]` and `B=[b_l,b_u]`:

```text
A + B = [a_l + b_l, a_u + b_u]
A - B = [a_l - b_u, a_u - b_l]
```

The same-operand subtraction identity returns `[0,0]`.

### Multiplication

For different operands:

```text
products = {a_l*b_l, a_l*b_u, a_u*b_l, a_u*b_u}
A * B = [min(products), max(products)]
```

For the same operand, the square relation is retained:

```text
lower = 0                         when a_l <= 0 <= a_u
        min(a_l*a_l, a_u*a_u)     otherwise
upper = max(a_l*a_l, a_u*a_u)
```

This avoids the false negative lower bound produced by treating two occurrences of the same signed
value as independent intervals.

### Division

Division uses Solidity's truncation toward zero. Candidate dividends are the two endpoints and zero
when present. Candidate divisors are the two nonzero endpoints and the closest-to-zero values
`-1`/`1` when present. The hull of the candidate quotients is conservative; exhaustive 2- and 3-bit
enumeration confirmed it for signed and unsigned intervals.

The existing state-owned nonzero-divisor continuation fact remains authoritative. Signed division
also records the `MIN / -1` no-overflow continuation fact, including unchecked code, because that
Solidity operation is exceptional rather than wrapping.

### Modulo

Modulo follows the dividend's sign. For divisor magnitude `d` and dividend magnitude `a`, the
remainder magnitude is bounded by:

```text
min(max_abs(A), max_abs(B) - 1)
```

Unsigned and nonnegative results use `[0,magnitude]`; nonpositive signed results use
`[-magnitude,0]`; a signed interval crossing zero uses the symmetric hull. Singleton operands are
evaluated exactly. Division by zero remains excluded by the state-owned continuation fact.

### Exponentiation

Fixed nonnegative exponents up to 1024 use endpoint/parity algebra. Bounded nonnegative base and
exponent intervals up to that cap evaluate endpoint candidates plus zero/one transition points.
Bases `-1`, `0`, and `1` have direct rules. A large singleton exponent with a singleton unchecked
base uses Python's modular `pow` and exact two's-complement decoding.

Negative, unbounded, or otherwise unsupported symbolic exponent cases return tagged top. Symbolic
power is not registered as an SMT equation: Z3 has no backend-neutral bit-vector exponent operator,
and the prior multiplication-shaped encoding had different semantics.

### Shifts

Shift counts from zero through the bit width are enumerated; all greater counts share Solidity's
width-or-greater result. Unsigned right shift is logical, signed right shift is arithmetic, and left
shift truncates bits even in a checked scope. A wrapping singleton is decoded exactly. A nonconvex
left-shift image returns top.

Only constant shifts receive an immutable SMT equation. Symbolic shifts remain abstract because
coercing the right operand to the left width can truncate a wider Solidity shift count and assert a
different equation.

### Bitwise operations

Singleton `AND`, `OR`, and `XOR` are exact. Same-operand identities and zero identities are exact.
For nonnegative intervals, `AND` uses `[0,min(a_u,b_u)]`; `OR` and `XOR` use a mask through the
highest possible set bit. General signed non-singleton bitwise cases return tagged top.

## Checked and unchecked semantics

For addition, subtraction, multiplication, and bounded power:

- when the mathematical interval fits the destination type, it is returned directly;
- checked arithmetic intersects the mathematical interval with the type range, so wrapped outputs
  are never included as successful results;
- an empty checked intersection becomes top because the current operation domain has no local
  bottom value; state-owned continuation facts still exclude infeasible addition, subtraction, and
  multiplication executions; and
- unchecked singleton overflow is wrapped and decoded exactly, while a non-singleton modular image
  that cannot be represented soundly by one interval becomes top.

Shifts always use truncating bit-vector semantics. Division and modulo use Solidity exceptional
conditions rather than unchecked wrapping.

The multiplication tests enumerate every operand-interval pair at 2- and 3-bit widths for signed
and unsigned, checked and unchecked modes. Every concrete successful product is contained by the
abstract interval.

## Abstract-first range policy

`solve_variable_range` sends an `abstract_range` to the Stage 2 range API when a tracked value is
finite or is the result of an operation. `Z3Solver.solve_range_result` then returns:

```text
feasibility = NOT_ATTEMPTED
lower_status = ABSTRACT
upper_status = ABSTRACT
sessions = ()
```

The returned fallback interval is the tracked abstract interval, including when it equals the full
type range. This makes solver-proven full range, abstract full range, and timeout full-range fallback
observably different in `RangeResult`, diagnostics, JSON, and telemetry.

Callers can request optional refinement with `RangeQueryConfig.refine_abstract=True`. The tracked
lower and upper bounds are then materialized as two typed `QUERY_LOCAL` facts using signed or
unsigned bit-vector comparisons. This prevents a model from being clamped after optimization and
incorrectly labeled `PROVEN`: every refined bound is now proved under the abstract interval, the
complete selected semantic state, and other query-local facts.

The refinement facts are ephemeral. Tests verify that three feasibility/lower/upper sessions
materialize six copies total while the `FunctionEncoding` fact IDs and `SemanticStateId` remain
unchanged.

## Total refinement budget

`QueryBudget` is a monotonic expression-wide wall-clock budget. One annotation budget is shared by:

1. the optional feasibility query;
2. the independent lower objective;
3. the independent upper objective; and
4. deferred unchecked overflow and underflow feasibility checks.

Range feasibility is established at most once. Minimum and maximum use fresh Stage 2
`QuerySession`/`Optimize` instances and preserve independent statuses. Before every session, the
remaining budget is recomputed. No session is admitted with less than 50 ms remaining. Each Z3
check receives a conservative fraction of the remaining budget and a watchdog interrupt, preventing
one soft timeout from consuming the budgets intended for all later objectives. Checks are serialized
because the installed Z3 binding uses the shared default context.

When a bound cannot run or finishes with `TIMEOUT`, `UNKNOWN`, or `ERROR`, only that side receives
the sound tracked fallback. A proven opposite bound is retained. Proven UNSAT feasibility still
returns the existing unreachable/bottom convention; unknown or timeout feasibility does not.

The deterministic fake-clock test spends 2 ms on feasibility, the remaining 8 ms on a successful
lower bound, skips the upper objective, and returns lower `PROVEN` plus upper `TIMEOUT`. A real
100 ms forced nonlinear refinement completed in about 76 ms, opened and closed two sessions, and
skipped the final objective. A 20 ms budget was rejected before session creation and returned a
tagged timeout fallback in about 0.05 ms.

## Status and telemetry

Stage 5 adds `FeasibilityStatus.NOT_ATTEMPTED`, `QueryBudget`, and `BoundOutcome` without changing
the Stage 2 meanings of `SAT`, `UNSAT`, `UNKNOWN`, `TIMEOUT`, `ERROR`, `PROVEN`, `ABSTRACT`, and
`NOT_ATTEMPTED`.

Opt-in telemetry now records:

- abstract-only decisions and refinement attempts;
- sessions avoided;
- configured total budget and wall elapsed time;
- budget exhaustion and partial results; and
- feasibility, lower, and upper status counts.

Session creation/closure, materialization counts, compatibility facts, assertion copies, and cleanup
imbalances remain owned by the Stage 2 telemetry. Telemetry stays disabled by default and is not a
semantic source of truth.

## Files and paths changed

- `analyses/interval/operations/binary/abstract_transfer.py`: backend-neutral transfer rules.
- `analyses/interval/operations/binary/arithmetic.py`: operation integration, continuation facts,
  abstract intervals, and safe suppression of unsupported power/symbolic-shift equations.
- `analysis.py`: abstract-first selection, tracked fallback, optional refinement-bound facts.
- `run_analysis.py`: one annotation-wide budget shared with deferred overflow checks.
- `smt_solver/query.py`: budgets, bound outcomes, diagnostics, and `NOT_ATTEMPTED` feasibility.
- `smt_solver/solver.py` and `smt_solver/__init__.py`: backend-neutral budget/result API exposure.
- `smt_solver/strategies/z3_solver.py`: budgeted feasibility and independent objective sessions,
  watchdog classification, partial-bound combination, and abstract results.
- `smt_solver/telemetry.py`: range-refinement metrics.
- `tests/e2e/data_flow/interval/solver_lifetime_probe.py`: abstract/refinement status, budget, timing,
  and session reporting plus forced-refinement mode.
- `tests/unit/analyses/data_flow/test_abstract_transfer.py`: multiplication soundness and
  representative nonlinear transfer tests.
- `tests/unit/analyses/data_flow/test_range_refinement.py`: no-session, budget, partial-result, and
  ownership tests.
- `tests/e2e/data_flow/interval/contracts/Test_AbstractTransfer.sol`: direct constant and bounded
  operation probes.
- `analyses/interval/LIMITATIONS.md`: Stage 5 precision and solver-policy limits.

No snapshot expectation was modified.

## Remaining `Optimize` call sites

There are three constructors in `z3_solver.py`, representing two semantic paths:

1. `Z3Solver(use_optimizer=True)` and its `reset()` branch retain the legacy reusable optimizer API,
   including `maximize()` and `minimize()`. The interval range path does not use this object.
2. `_create_optimizer_backend()` creates one fresh `Optimize` owned by one lower- or upper-bound
   `QuerySession`. This is the only `Optimize` constructor used by Stage 5 refinement.

No objective is retained across independent range queries.

## Query-count and timing comparison

The pre-implementation Stage 4 audit and current probes used opt-in telemetry:

| Scenario | Stage 4 query behavior | Stage 5 result |
|---|---|---|
| unconstrained checked `uint256 x*y` | 3 sessions, about 100 ms, timeout fallback | abstract top, 0 sessions, about 0.03 ms |
| branch-bounded `x=[10,99]; x*2` | 3 sessions, about 45 ms | abstract `[20,198]`, 0 sessions, about 0.03 ms |
| fixed-loop `sum_2` at four states | 12 explicit sessions; analysis already used 0 | four abstract `[0,45]` results, 0 sessions, about 0.07 ms total |
| forced nonlinear refinement, 100 ms | each subquery could receive a full timeout | 2 balanced sessions, about 76 ms total, final objective skipped |

The timing values are machine-local observations, not performance assertions. Query counts and
statuses are deterministic architectural results.

## Verification

### Unit and static checks

```text
.venv/bin/pytest -q tests/unit/analyses/data_flow/
113 passed

.venv/bin/ruff check <all modified Python files>
passed

.venv/bin/python -m compileall -q slither/analyses/data_flow \
    tests/unit/analyses/data_flow tests/e2e/data_flow/interval/solver_lifetime_probe.py
passed

ty check --python .venv \
    abstract_transfer.py analysis.py query.py
passed

git diff --check
passed
```

A broader `ty` run over `arithmetic.py`, `run_analysis.py`, `z3_solver.py`, and `telemetry.py` is not
a clean repository gate: it reports 60 broad typing diagnostics, principally in existing SlithIR
operand unions, nullable interval domains/models, the coarse `SMTTerm` Z3 union, and the undeclared
`rich.table` module. Stage 5 did not add ignores or install dependencies to mask that debt.

An additional exhaustive audit enumerated all 2- and 3-bit intervals for division, modulo, power,
shifts, and bitwise operations under the relevant signed/unsigned and checked/unchecked modes. Every
concrete successful result was contained by the abstract interval.

### Direct probes

All probes used Solidity 0.8.20. Every row ended with zero active sessions, zero cleanup imbalances,
zero persistent backend assertions, zero duplicate reusable assertions, and zero internal reusable
unclassified additions.

| Scenario | Result | Query lifecycle |
|---|---|---|
| unconstrained checked multiplication | abstract unsigned top | 0 sessions |
| signed checked multiplication | abstract signed top | 0 sessions |
| unchecked multiplication | abstract unsigned top, wrap possible | 0 sessions |
| branch-bounded multiplication | `[20,198]` | 0 sessions |
| constant power `3**2` | `[9,9]` | 0 sessions |
| constant bitwise `10 & 12` | `[8,8]` | 0 sessions |
| constant division `10/5` | `[2,2]` | 0 sessions |
| constant modulo `10%5` | `[0,0]` | 0 sessions |
| constant left shift `10<<2` | `[40,40]` | 0 sessions |
| signed right shift `-10>>2` | `[-3,-3]` | 0 sessions |
| fixed loop | 39 iterations; `sum_2=[0,45]` | analysis 0; four range results 0 |
| storage store/load | `x_1=[42,42]` | 0 sessions |
| internal chained call | final result `[30,30]` | analysis 0; explicit result query 3/3 |
| concrete high-level chained call | final result `[30,30]` | analysis 0; explicit result query 3/3 |
| forced refinement, 20 ms | tagged timeout top | 0 sessions; rejected by admission policy |
| forced refinement, 100 ms | tagged timeout top | 2/2 sessions; about 76 ms wall time |

### Snapshot blocker

The snapshot command was attempted without update mode:

```text
SOLC_VERSION=0.8.20 .venv/bin/pytest -q tests/e2e/data_flow/interval/
25 setup errors: ModuleNotFoundError: No module named 'rich'
```

The missing dependency is imported by `source_view.py`, before any snapshot comparison runs. It was
not installed or added as part of Stage 5. Direct engine probes provide the integration evidence in
this environment.

## Observable behavior changes

- Finite operation results and operation-derived top now return tagged abstract bounds without
  solver feasibility or optimization.
- Optional refinement proves bounds under typed query-local copies of the tracked abstract interval.
- Minimum and maximum retain independent statuses and one successful side is no longer discarded.
- Timeout, unknown, error, abstract, and proven full ranges remain distinct.
- Symbolic power no longer receives an incorrect multiplication equation.
- Symbolic shifts no longer receive an equation after potentially lossy width matching.
- Signed `MIN / -1` continuation semantics are recorded explicitly.

These changes restore sound operation semantics or make proof provenance explicit. No expected
snapshot output was changed automatically.

## Remaining precision limits

1. `require` and branch relations remain state-owned facts and do not always narrow operand
   intervals before abstract transfer. The result can therefore be top even when optional SMT
   refinement could recover a tighter bound.
2. A one-interval domain cannot represent most modular images. Non-singleton unchecked wrap returns
   top rather than an unsound narrow hull.
3. General signed non-singleton bitwise operations return top.
4. Symbolic or very large power returns top unless a safe singleton rule applies; there is no
   exponent SMT relation.
5. Symbolic shifts are abstract-only; they intentionally lose relational solver refinement.
6. A guaranteed checked failure can remain top when the operation layer has no local bottom. The
   existing continuation facts preserve infeasibility for addition, subtraction, multiplication,
   division, and modulo, but there is no general power-overflow fact.
7. An abstract-only result has feasibility `NOT_ATTEMPTED`; it is not a solver proof that the selected
   semantic state is reachable.
8. The 50 ms session admission floor and fractional backend allocation are conservative. They favor
   prompt, tagged fallback over attempting a session unlikely to complete.
9. The reusable `Z3Solver(use_optimizer=True)` compatibility surface remains, although interval
   refinement uses only fresh session-owned optimizers.

These limits are explicit conservative losses of precision. They do not require changes to Stage 3
joins, Stage 4 widening, or the worklist to maintain soundness.
