# Stage 2 Query Sessions Report

## Scope and outcome

Stage 2 splits the persistent per-function SMT role into a reusable `FunctionEncoding` and
disposable `QuerySession` instances. The interval engine now materializes range, feasibility,
require/assert, overflow, and underflow queries from typed facts without adding those facts to the
reusable backend solver.

The public `solve_range(term, extra_constraints=None, timeout_ms=..., signed=...)` shape remains
available. Its implementation delegates to `solve_range_result`, and `Z3Solver.last_range_result`
retains the richer result when a legacy caller needs the tuple representation.

No join, widening rule, loop-edge rule, phi rule, worklist policy, nonlinear optimizer strategy,
abstract multiplication fallback, or public analysis entry point was intentionally changed.

## Final design

`smt_solver/query.py` contains the backend-neutral lifecycle types:

- `FunctionEncoding` owns the `EncodingId`, encoding version, stable symbol registry, immutable
  equations, context equations, and their Stage 1 provenance.
- `QueryMaterialization` is a frozen snapshot of one encoding, exactly one `SemanticStateId`, its
  exact active state facts, typed query-local facts, one purpose, and at most one selected property
  obligation.
- `QuerySession` owns one materialization, timeout, backend solver or optimizer instance, elapsed
  time, outcome diagnostics, and cleanup validation. It releases its backend on every close path.
- `FeasibilityResult` and `RangeResult` expose typed results and serializable diagnostics.

`SMTSolver.register_immutable_fact` now registers into `FunctionEncoding` only. It no longer calls
the reusable backend `_add_constraint`. `solver.variables` aliases the encoding's symbol registry
for source compatibility.

`SMTSolver.create_query_session` snapshots the encoding and property registry, validates that the
materialized state fact IDs equal `SemanticStateId.active_fact_ids`, and wraps any guarded backend
compatibility assertions or raw compatibility constraints as ephemeral query-local facts.

Z3 materialization occurs only after this backend-neutral validation. A fresh `Solver` is created
for feasibility, and separate fresh `Optimize` instances are created for minimum and maximum.
There is no reusable `Optimize` instance and no accumulation of objectives.

## Ownership and lifetime rules

| Owner | May contain | Lifetime | Prohibited content |
|---|---|---|---|
| `FunctionEncoding` | symbols, immutable equations, context equations, immutable provenance | one function analysis | branch facts, continuation facts, checked-success facts, query assumptions, objectives, properties, timeout state |
| `State` | branch guards, successful require/assert conditions, checked-arithmetic continuation facts, other path facts | one abstract state | immutable definitions, objectives, solver timeout state, property activation |
| `QuerySession` | one encoding snapshot, one exact state snapshot, query-local facts, optional selected property, one backend, timeout and outcome data | one feasibility or objective query | persistent mutation of the encoding, state, property registry, or reusable backend |

`QueryMaterialization.__post_init__` rejects owner mismatches. It also rejects a state fact set that
does not exactly match the selected `SemanticStateId`. Ordinary range and feasibility sessions do
not inspect or materialize the property registry. An explicit property session may select one
previously registered obligation; no other obligation is activated.

Overflow and underflow checks intentionally use a typed branch-only semantic view. The view retains
the state's abstract values and provenance but replaces `active_fact_ids` with exactly the branch
facts being materialized. This preserves the existing exclusion of checked-arithmetic success facts,
which would otherwise make an overflow query tautologically safe, without mutating the source state.

## Result statuses

The rich APIs distinguish:

- feasibility: `SAT`, `UNSAT`, `UNKNOWN`, `TIMEOUT`, and `ERROR`;
- each bound: `PROVEN`, `ABSTRACT`, `UNKNOWN`, `TIMEOUT`, `ERROR`, and `NOT_ATTEMPTED`.

`RangeResult` carries independent lower and upper values and statuses, an optional tagged fallback
interval, encoding and state identities, and all subquery diagnostics. `RangeResult.to_dict()` and
the diagnostic serializers preserve these distinctions.

The compatibility wrapper maps fully proven or explicitly abstract bounds to legacy `SUCCESS` and
UNSAT feasibility to `UNSAT`. When either bound remains unproven, a timeout maps to `TIMEOUT` and
other inconclusive cases map to legacy `ERROR`. The complete distinctions remain available in
`last_range_result`.

## Timeout, unknown, error, and partial-bound behavior

Feasibility is checked once per `solve_range_result` invocation. UNSAT produces the existing bottom
convention and does not create objective sessions. UNKNOWN, TIMEOUT, and ERROR are not treated as
unreachable. The minimum and maximum objectives are still attempted independently after an
inconclusive feasibility result, preserving the existing nonlinear three-query strategy.

Z3 unknown results are classified as TIMEOUT when Z3 reports timeout/cancellation or when an opaque
unknown consumes at least 90 percent of the configured timeout. Other unknown results remain
UNKNOWN. Backend exceptions become ERROR diagnostics. Python exceptions still close the session and
then propagate when they occur outside the typed backend-error conversion boundary.

If one objective succeeds and the other times out, is unknown, or errors, the proven side is kept.
Only the failed side receives the sound type fallback. A proven `[0, MAX]`, timeout fallback
`[0, MAX]`, and explicitly abstract `[0, MAX]` serialize with `PROVEN`, `TIMEOUT`, and `ABSTRACT`
bound statuses respectively.

Non-proven fallback results are not inserted into the existing annotation range cache. Typed cache
keys use the function encoding identity plus `SemanticStateId`; raw legacy path formulas disable
that cache rather than using formula text as semantic identity.

## Query cleanup guarantee

Session construction captures:

- `FunctionEncoding` fact IDs;
- property-obligation fact IDs;
- guarded reusable-backend assertion identities;
- reusable backend push/pop depth.

Session close releases the owned backend, decrements the active-session counter, compares the live
persistent surfaces with the snapshot, and records any imbalance. The snapshot deliberately does not
require stack-ordered session closure, so two independent live sessions can close in either order.

Focused tests cover SAT, UNSAT, TIMEOUT, UNKNOWN, backend ERROR, and a raised Python exception. They
also cover two overlapping sessions with opposite assumptions. Every tested path retains the same
encoding fact IDs, state semantic ID, property registry, and reusable backend assertions and ends
with zero active sessions.

## Migrated files and query paths

- `smt_solver/query.py`: new backend-neutral encoding, materialization, session, status, result, and
  serialization types.
- `smt_solver/solver.py`: `FunctionEncoding` ownership, typed materialization, session creation,
  cleanup snapshots, property selection, and abstract rich-query interfaces.
- `smt_solver/strategies/z3_solver.py`: isolated feasibility and independent objective sessions,
  rich result construction, compatibility wrapper, timeout classification, and removal of the four
  raw range assertion-copy sites.
- `smt_solver/facts.py`: ephemeral compatibility query-fact construction without formula-derived
  identity.
- `smt_solver/telemetry.py`: session lifecycle, materialization, status, timeout, elapsed-time,
  assertion-copy, compatibility, and cleanup metrics.
- `analysis.py`: typed annotation/legacy range inputs, rich partial-bound consumption, typed overflow
  feasibility, semantic cache keys, and non-proven cache exclusion.
- `analyses/interval/analysis/analysis.py`: function encoding binding and typed widening range
  materialization. The existing choice to solve both widening values under the current state remains
  unchanged.
- `analyses/interval/core/state.py`: typed branch-fact access and non-mutating semantic fact-subset
  views.
- `analyses/interval/operations/solidity_call/require_assert.py`: isolated continuation feasibility
  with separate `REQUIRE` and `ASSERT` purposes.
- `run_analysis.py`: exact-state annotation ranges and isolated branch-only overflow/underflow
  sessions.
- `tests/e2e/data_flow/interval/solver_lifetime_probe.py`: typed state queries and Stage 2 session
  telemetry in direct probes.

## Remaining compatibility and backend paths

The remaining raw public compatibility path is `solve_range(extra_constraints=...)`. Each formula is
wrapped as a `QUERY_LOCAL` fact with `FactKind.COMPATIBILITY` and compatibility provenance. It is
materialized independently in feasibility, minimum, and maximum sessions, increments compatibility
query telemetry, never enters `FunctionEncoding` or `State`, and never increments reusable-backend
unclassified additions.

The guarded `assert_constraint` and scoped `add_query_local_assumption` APIs remain for legacy callers.
The Stage 1 interval engine no longer uses them for range, require/assert, overflow, or underflow
queries. `assert_constraint` additions are treated as reusable-backend compatibility inputs when a
session is materialized.

The remaining direct backend formula-addition sites are:

1. `Z3Solver._add_constraint`, used only by the guarded reusable-backend compatibility API;
2. feasibility-session `Solver.add` from `QueryMaterialization.facts`;
3. per-objective `Optimize.add` from `QueryMaterialization.facts`.

No code copies `self.solver.assertions()` directly into range feasibility or optimization contexts.

## Telemetry

Opt-in telemetry now records:

- sessions created, closed, active, and maximum active;
- cleanup imbalances;
- purpose, `EncodingId`, and `SemanticStateId`;
- immutable, state, query-local, compatibility, and property facts materialized;
- assertion-copy/materialization counts;
- feasibility and bound statuses;
- configured timeout sessions, actual timeout results, and elapsed milliseconds.

Telemetry remains disabled by default and is not used to determine query semantics.

## Focused tests

`tests/unit/analyses/data_flow/test_query_sessions.py` covers:

- encoding and state immutability across success, UNSAT, timeout, unknown, error, and exception;
- opposite-assumption query isolation and out-of-order close;
- state A (`x < 10`) versus state B (`x > 20`) isolation;
- partial lower success with upper timeout, unknown, or error;
- proven, timeout-fallback, and abstract full-range tagging and serialization;
- raw `extra_constraints` compatibility telemetry and cleanup;
- ordinary versus explicitly selected property materialization;
- require and assert cleanup for SAT, UNSAT, timeout, and backend error;
- state-ID/fact-set mismatch rejection;
- typed overflow state and query-fact materialization.

Stage 1 ownership tests were updated only where the required Stage 2 semantic boundary changed:
immutable facts are now absent from the reusable backend assertion list. The reusable compatibility
telemetry test now verifies that its two legacy assertions remain unchanged after three sessions.

## Verification results

Commands run successfully:

```text
.venv/bin/pytest -q tests/unit/analyses/data_flow/
35 passed

git ls-files -m -o --exclude-standard '*.py' | xargs .venv/bin/ruff check
All checks passed

git ls-files -m -o --exclude-standard '*.py' |
  xargs .venv/bin/python -m compileall -q
completed successfully

ty check --python .venv slither/analyses/data_flow/smt_solver/query.py \
  slither/analyses/data_flow/smt_solver/solver.py \
  slither/analyses/data_flow/analysis.py
All checks passed
```

A broader targeted `ty` run is now possible through the global executable, although `.venv/bin/ty`
is still absent. It reports 37 existing diagnostics in the interval engine, runner, and pre-existing
Z3 term-union methods. The new backend-neutral query/session files and the migrated core range helper
pass targeted type checking. No ignores were added for unrelated typing debt.

## Direct probes

All probes used Solidity 0.8.20, opt-in ownership telemetry, and the typed probe path.

| Scenario | Result | Lifecycle result |
|---|---|---|
| symbolic addition | SAT, proven `[0, uint256 MAX]` | 3/3 sessions closed |
| symbolic multiplication, 250 ms | feasibility/lower/upper TIMEOUT, tagged full fallback | 3/3 sessions closed |
| fixed-bound loop | 13 worklist iterations, unchanged from Stage 1; 16 range invocations | 48/48 sessions closed |
| branch condition | true-branch `x` proven `[0, 9]`; 5 worklist iterations | 21/21 sessions closed |
| require | successful continuation `x < 100`; `REQUIRE` purpose observed | 4/4 sessions closed |
| assert | successful continuation `x < 100`; `ASSERT` purpose observed | 4/4 sessions closed |
| checked addition | result range queries proven | 6/6 sessions closed |
| storage load/store | stored and loaded value proven `42` | 12/12 sessions closed |
| internal call | `_addTen(5)` result proven `15` | 6/6 sessions closed |
| high-level call | call equation materialized without backend persistence | 3/3 sessions closed |

Every probe ended with zero active sessions, zero cleanup imbalances, zero duplicate reusable backend
assertions, zero live reusable backend assertions, zero internal reusable unclassified additions, and
zero compatibility query facts. The compatibility-only unit test separately observes the expected
ephemeral compatibility query count.

## Snapshot and environment blockers

The snapshot runner still cannot import because `rich` is absent from the existing `.venv`:

```text
ModuleNotFoundError: No module named 'rich'
```

No dependency was installed, no snapshot expectation was modified, and no existing snapshot was
accepted automatically. Direct engine probes cover the same transfer categories without importing
the annotated source renderer.

## Observable behavior changes

The intentional Stage 2 behavior changes are limited to ownership and result observability:

- immutable/context equations no longer appear in `get_assertions()`; that method now reflects only
  guarded reusable-backend compatibility assertions;
- `to_smtlib()` serializes both `FunctionEncoding` facts and guarded compatibility assertions;
- timeout, unknown, error, proven, and abstract range outcomes are distinguishable;
- a successful one-sided objective is retained in the rich result;
- non-proven fallbacks are tagged and not cached as solver proofs;
- raw external `extra_constraints` are visible as ephemeral compatibility telemetry, not reusable
  unclassified additions.

No snapshot output is intended to change. Full-type fallback values remain conservative, and the
legacy wrapper retains its source-level call and tuple shape.

## Recommended Stage 3 entry point

Begin Stage 3 at `IntervalDomain._merge_states` in
`analyses/interval/analysis/domain.py`. It currently unions predecessor variable names but does not
join complete `State` components or use `SemanticStateId` to decide convergence.

The first Stage 3 tests should build the same predecessor set in different arrival orders and require
identical joined `SemanticStateId` values. The join must explicitly define behavior for abstract
values, active fact IDs, branch-fact classification, storage summaries, comparisons, dependencies,
and context identity. Then update `Forward.apply_transfer_function` to compare the complete stored
input semantic identity before and after join, without changing worklist topology or widening policy.

Stage 3 should not reuse `QuerySession` as a state container. It should produce one complete,
order-independent joined `State`; future queries will then materialize that exact state through the
Stage 2 boundary.
