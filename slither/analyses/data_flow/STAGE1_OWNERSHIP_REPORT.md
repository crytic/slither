# Stage 1 Ownership Foundation

## Result

Stage 1 introduces backend-neutral semantic identities and typed ownership boundaries without
changing the worklist topology, public analysis entry points, `solve_range` call shape, join
algorithm, widening policy, nonlinear solver strategy, or property-checking behavior.

Immutable equations are now idempotent by semantic `FactId`. State-local facts are stored in a
deduplicating registry owned by `State`. Z3 expression text remains diagnostic telemetry only;
it is not used as semantic identity.

## Type and ownership model

`smt_solver/facts.py` defines:

- `EncodingId`: source unit, canonical function identity, and encoding version.
- `StaticOperationId`: encoding, CFG node ID, and static SSA IR position.
- `AnalysisContextId`: encoding plus structured call, storage, and summary paths.
- `FactProvenance`: origin, context, operation/edge, loop generation, and property slots.
- `FactId` and generic `Fact`: owner, semantic kind, provenance, role key, and formula.
- `FactRegistry`: insertion-ordered storage deduplicated by `FactId`.
- `SemanticStateId`: reachability, context, abstract values/bounds, active fact IDs, storage,
  comparisons, and dependencies.

The ownership classes are immutable equation, context equation, state local, loop generation,
query local, property obligation, and unclassified compatibility. The solver exposes one typed
boundary for each class. Loop-generation registration is explicitly unsupported until it has a
generation-scoped session. Property obligations are registered as checker data and are not
asserted. Query-local assumptions require an active balanced solver scope.

## Migrated formula sites

- Immutable/context equations: assignment; arithmetic and comparison results; unary; delete;
  type conversion; phi and phi callback; return; unpack; index; member; array initialization;
  uninitialized defaults; storage bindings; and interprocedural parameter/result bindings.
- State-local facts: CFG branch guards, checked-arithmetic success conditions, nonzero
  divisors, and successful `require`/`assert` continuation.
- Query-local facts: `require` feasibility and overflow/underflow checks in the range and
  annotation paths.
- Loop-generation facts: the threshold-bound producer is typed and fails explicitly because
  Stage 2 has not added generation-scoped sessions.
- Property obligations: the typed registry exists; Stage 1 adds no production property
  producer.

The core migration spans `smt_solver/facts.py`, `solver.py`, `z3_solver.py`, and `telemetry.py`.
State/context changes are in `core/state.py`, `analysis/domain.py`, and `analysis/analysis.py`.
Formula producers were migrated across the interval `operations/` handlers, with temporary
overflow queries updated in `data_flow/analysis.py` and `run_analysis.py`.

The common handler APIs in `operations/base.py` and `operations/type_utils.py` construct facts
from operation, node, context, origin, and semantic role. Interprocedural equations retain their
static operation identity while call context is represented separately from display-only symbol
prefixes. The prefixes themselves are now derived from the structured call path instead of
process-global traversal counters. Storage equations similarly use a storage child context.

`State.deep_copy` shares immutable `Fact` values and copies every mutable container. Top and
bottom domains retain their function context, so reachability and context both participate in
semantic state identity.

## Telemetry

Opt-in telemetry reports registrations and duplicate attempts grouped by owner, origin, and the
complete analysis-context key. The earlier structural `sexpr()` duplicate counter remains a
backend diagnostic and is not presented as semantic identity. The guarded `assert_constraint`
compatibility API increments both a solver-local unclassified counter and telemetry.

The loop probe for `test_fixed_bound_loop` reported:

- 15 classified registrations: eight immutable and seven state-local;
- three semantic duplicate-registration attempts, all deduplicated;
- six live backend assertions and zero duplicate backend assertions;
- zero unclassified additions across 13 worklist iterations.

## Remaining compatibility and direct-addition paths

- `SMTSolver.assert_constraint` remains source-compatible for external callers, but every use is
  marked unclassified. No active interval-analysis producer calls it.
- `solve_range(extra_constraints=...)` still accepts raw formulas. Z3 copies the reusable
  assertions and those formulas into fresh feasibility/optimization solvers at
  `z3_solver.py:727`, `:731`, `:763`, and `:767`. These are ephemeral query materialization
  sites, not reusable-solver registrations, but they do not yet retain typed fact provenance.
- `Z3Solver._add_constraint` is the sole reusable-backend addition site
  (`z3_solver.py:170`) and is protected by the ownership-aware solver APIs.
- Loop-generation materialization and property-query materialization intentionally remain
  unsupported rather than falling back to permanent assertions.

## Verification

Commands and results:

```text
.venv/bin/pytest -q tests/unit/analyses/data_flow/
12 passed

.venv/bin/ruff check <all modified Python files>
All checks passed

.venv/bin/python -m compileall -q <all modified Python files>
passed
```

The idempotence tests were mutation-checked by temporarily making duplicate registry insertion
return success. Both immutable and state-local idempotence tests failed, and passed again after
restoring the implementation.

Direct engine probes passed for addition, the fixed-bound loop, branch conditions, `require`,
internal/library/high-level calls, tuple calls, storage load/store, and array initialization.
Every probe ended with zero duplicate backend assertions. The loop had 13 iterations; the
others retained their existing worklist shapes. The symbolic multiplication probe registered
one immutable and one state-local fact with no duplicates or unclassified additions; its
250ms bound optimizations returned the existing `error` timeout outcome, as expected because
nonlinear solving is unchanged in Stage 1.

The selected snapshot tests could not reach analysis because `source_view.py` imports `rich`,
which is absent from the existing `.venv` and is not declared for this test environment. Six
selected cases failed during fixture import with `ModuleNotFoundError: rich`. Direct probes of
the same analysis engine were used instead. The `ty` executable is also absent from `.venv`.
Neither dependency was added as part of this ownership-only stage.

No snapshots were modified.

## Stage 2 entry point

Split the current per-function solver role at `SMTSolver.register_immutable_fact` and
`Z3Solver.solve_range`:

1. Build an immutable `FunctionEncoding` from the persistent immutable/context `FactRegistry`.
2. Create a short-lived `QuerySession` from that encoding plus one `SemanticStateId` and its
   typed state facts.
3. Materialize query assumptions and a property obligation only inside the session.
4. Replace the four raw range-query copy sites with session construction while preserving the
   public `solve_range` compatibility wrapper.

This boundary addresses query isolation next without prematurely changing join, widening, or
nonlinear fallback semantics.
