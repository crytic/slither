# Stage 3 State Join Report

## Scope and outcome

Stage 3 replaces first-predecessor interval-state merging with a complete, conservative,
non-disjunctive join. Reachable predecessor states now join deterministically across abstract
values, active facts, storage summaries, comparison metadata, dependency data, and analysis
context. Worklist propagation uses the complete `SemanticStateId` to decide whether a successor
input changed.

The Stage 1 fact identities and the Stage 2 `FunctionEncoding`/`QuerySession` ownership boundary
remain authoritative. A joined state is still ordinary state data; it is not a solver session or a
set of reusable backend assertions.

No worklist edge, widening trigger, loop-edge rule, nonlinear strategy, public analysis entry
point, property behavior, or range-result status was intentionally changed.

## Complete State inventory

| Component | Representation | Join rule | Semantic identity |
|---|---|---|---|
| Reachability | `IntervalDomain.variant` | `BOTTOM` is identity; `TOP` is absorbing; two states remain reachable | `SemanticStateId.reachability` |
| Function/context | `AnalysisContextId` | equal contexts survive; unbound bottom/top is neutral; incompatible bound contexts raise | `context_id` |
| Variable environment | name to immutable `TrackedSMTVariable` | union of names; common variables use the interval least upper bound | `abstract_values` |
| Numeric value | `NumericInterval` | closed interval hull | lower and upper bounds |
| Path totality | `TrackedSMTVariable.is_total` | logical AND for common variables; false for one-path definitions | `AbstractValueId.is_total` |
| Overflow metadata | predicates, stable operation ID, unchecked flag | static identities must agree; predicate expressions must agree; unchecked is may-information | operation ID, predicate presence, unchecked flag |
| Explicit state facts | typed `FactRegistry` | exact `FactId` intersection | `active_fact_ids` |
| Derived range facts | typed `RANGE_BOUND` facts | regenerated from the final total abstract values | `active_fact_ids` |
| Branch view | filtered explicit fact registry | derived after join; never independently merged | covered by active fact IDs |
| Storage | slot to `StorageSlotSummary` | may-write union; missing slot sets `may_be_unwritten` | slot, write names, unwritten flag |
| Comparisons | boolean SSA name to `ComparisonInfo` | intersection by stable operation ID and interval refinements | operation ID and refinements |
| Dependencies | name to may-dependency set | union | sorted dependency edges |
| Memory | no state component | not modeled; assembly/Yul memory operations fail explicitly | none |
| Aliases/references | no separate alias component | no hidden first-predecessor state; scalar reference/index/member values use the variable environment and may-dependencies | variable and dependency identity |
| Properties | Stage 2 property registry, not `State` | never joined or materialized by ordinary range queries | outside state identity |
| Diagnostics | opt-in telemetry | counters combine independently of semantics | intentionally excluded |

The handler inventory found no other mutable state surface. Call and storage context is contained in
the structured `AnalysisContextId`; query caches already key state-sensitive results by
`SemanticStateId`.

## Join algorithm

`IntervalDomain.join` handles lattice reachability and context compatibility. For two reachable
states it calls the pure `State.joined` operation, compares complete semantic identities, and stores
the result only when it changed.

`BOTTOM` and `TOP` identities contain only reachability and context. Any transient builder payload
retained while an operation terminates is not treated as reachable abstract state and cannot make
two bottom values semantically different.

`State.joined` performs these steps:

1. Require equal structured analysis contexts.
2. Join every common variable with an interval hull after validating name, sort, type range,
   signedness, and width compatibility.
3. Mark a variable present on only one predecessor as path-optional.
4. Intersect explicit facts by `FactId` and validate that a shared ID still maps to the same formula.
5. Intersect comparison metadata by stable operation identity and refinements.
6. Union may-dependencies.
7. Union storage may-writes and record whether any path may leave a slot unwritten.
8. Rebuild derived range facts and branch views from the final joined state.

All iterations and serialized identities use sorted structured keys. Formula `sexpr()` text is not
used as fact, comparison, state, or join identity. Formula equality is only a defensive validation
of the Stage 1 contract that one shared `FactId` cannot denote two formulas.

The focused algebra tests establish commutativity, idempotence, associativity for the represented
components, and bottom identity. `TOP` remains absorbing.

## Missing-variable semantics

A definition present on only one reachable predecessor is retained as a path-optional abstract
value (`is_total=False`) rather than being treated as an unconditional narrow value. Its conditional
interval remains available to phi and diagnostic handling, but it emits no unconditional range
fact. Arithmetic consumers treat a path-optional operand as unknown, assignments preserve
optional totality, storage writes fall back to the type range, and phi results remain optional
unless every static incoming value exists. Path-optional phi alternatives collectively cover their
associated predecessor edges, so a complete phi remains total.

This is conservative for the existing SSA representation and avoids both blindly copying the
present predecessor's bounds and inventing a definition on the absent path.

## Facts and QuerySession integration

Only explicit facts with identical `FactId` values in every reachable predecessor survive. Thus a
guard and its negation, checked-add versus checked-sub success, or a require continuation present on
one path do not become unconditional after the join. A common fact survives once. Structurally equal
formulas with different provenance do not become common.

State-derived interval bounds are typed `STATE_LOCAL/RANGE_BOUND` facts with
`ABSTRACT_STATE` provenance. `State.semantic_id().active_fact_ids` and `State.get_facts()` are built
from the same final explicit-plus-derived registry. The Stage 2 exact-state validation therefore
accepts a joined state without a compatibility path. Focused tests verify that materialization
contains no predecessor-exclusive facts and leaves the encoding and state unchanged.

## Storage, memory, comparison, alias, and dependency behavior

Storage summaries are may-information. Different writes to the same slot are unioned. A slot
missing from one predecessor is marked `may_be_unwritten`, so a later load cannot assume that the
modeled write occurred. `sstore` transfers the stored value's interval into its stable write symbol;
`sload` uses the hull of all complete modeled write values and otherwise returns the full type
range.

The previous `sload` implementation created an immutable equation from the state-dependent set of
writes visible at traversal time. That equation violated both Stage 1 immutability and Stage 3 order
independence. It was replaced with state-owned abstract transfer and derived range facts. The
storage probe still proves the stored and loaded constant `42`.

Memory and a separate may-alias lattice do not exist in this interval engine. Assembly/Yul memory
operations are rejected before transfer with `NotImplementedError`; the direct memory probe confirms
that explicit behavior. Reference, member, and index results are tracked as scalar SSA values, and
their may-dependencies use union. No implicit memory or alias container is selected from the first
predecessor.

Comparison metadata survives only when both predecessors carry the same stable operation identity
and interval refinements. May-dependencies are unioned so a possible source is never omitted.

## Immutability and convergence

`State.deep_copy` copies every mutable semantic container while sharing frozen facts, identities,
intervals, comparison records, storage summaries, and tracked wrappers. `State.joined` constructs a
new state and never mutates either predecessor.

Forward transfer now follows this lifecycle:

1. Take the stored node input.
2. Deep-copy it into an exclusive mutable output builder.
3. Run the existing transfer sequence on that builder.
4. Store the builder as the node output.
5. Apply the existing condition and widening branches.
6. Join into each stored successor input.
7. Enqueue the successor only when its complete `SemanticStateId` changes.

An identical second propagation is a semantic no-op and does not rerun the successor transfer.
Changes limited to facts, intervals, storage, comparisons, or dependencies all change identity and
cause propagation. The worklist topology and back-edge branches are unchanged.

Widening still uses its existing trigger and numeric algorithm. Its output builder now deep-copies
the current complete state before replacing widened numeric values, preventing unrelated facts,
storage, comparisons, or dependencies from disappearing. This is state preservation, not a Stage 4
widening-policy change.

Phi equations retain the existing selected-values policy. Their immutable equation now enumerates
all statically declared incoming SSA symbols, independent of predecessor arrival; the abstract phi
value uses the hull of the incoming values currently present. This is the minimum change needed to
remove first-predecessor equation construction.

## Files and paths changed

- `analyses/interval/core/state.py`: complete state inventory, pure component joins, derived range
  facts, stable semantic identity, copying, and storage summaries.
- `analyses/interval/core/tracked_variable.py`: numeric intervals, path totality, and stable overflow
  metadata.
- `analyses/interval/analysis/domain.py`: lattice join and full-state change detection.
- `engine/domain.py`, `engine/direction.py`, and `engine/analysis.py`: generic deep-copy transfer
  contract and exclusive forward output builders.
- `analyses/interval/analysis/analysis.py`: branch interval refinement, complete widening copies, and
  stable widening metadata.
- assignment, arithmetic, comparison, phi, phi-callback, `sstore`, and `sload` handlers: sound
  abstract-value production needed by the complete state join.
- `analysis.py`: annotation metadata reads the complete abstract interval.
- `smt_solver/facts.py`: complete `AbstractValueId` and `SemanticStateId` fields plus abstract-state
  provenance.
- `smt_solver/telemetry.py` and `solver_lifetime_probe.py`: opt-in join/convergence observations.
- legacy interval and reentrancy domains: deep-copy/signature conformance required by the engine
  transfer contract; their join policies were not otherwise changed.
- `tests/unit/analyses/data_flow/test_state_join.py`: focused Stage 3 algebra, ownership,
  materialization, mutation, branch arithmetic, telemetry, and revisit tests.

## Focused tests

The Stage 3 tests cover:

- both predecessor orders across every represented state component;
- idempotence and three-state associativity;
- bottom identity and top absorption;
- unsigned, signed, nested, and top interval hulls;
- path-optional missing definitions;
- storage equality/difference/missing-path behavior;
- common, exclusive, and structurally-equal-but-distinct facts;
- common and exclusive comparison metadata;
- may-dependency union;
- incompatible contexts;
- predecessor and stored-input immutability;
- exact Stage 2 query materialization and balanced cleanup;
- no-op revisit suppression and reruns for complete-state changes;
- stable overflow-operation identity;
- the required branch arithmetic result in both predecessor orders.

For the required example, both orders produce:

```text
x = [0, MAX_UINT256]
y = [10, MAX_UINT256 - 10]
active exclusive guards = none
active exclusive checked-arithmetic facts = none
```

The joined `y` query proves the same interval and closes all sessions.

## Verification results

Commands completed successfully:

```text
.venv/bin/pytest -q tests/unit/analyses/data_flow/
56 passed

.venv/bin/ruff check <all modified Python files>
All checks passed

.venv/bin/python -m compileall -q <modified data-flow and test paths>
completed successfully

ty check --python .venv <modified Stage 3 core files>
All checks passed

git diff --check
completed successfully
```

The `.venv/bin/ty` path is absent, but the available global `ty` executable passes the targeted core
check. A repository-wide ruff invocation reports 354 pre-existing modernization diagnostics; the
required modified-file invocation is clean. No modified Python function exceeds 80 lines and no
modified Python line exceeds 100 characters.

## Direct probes

All probes used Solidity 0.8.20 and opt-in telemetry.

| Scenario | Semantic result | Lifecycle result |
|---|---|---|
| branch condition | true `x=[0,9]`, false `x=[10,MAX]`; 5 iterations | 21/21 sessions, no imbalance |
| reversed predecessor order | identical `SemanticStateId`, facts, and hulls in focused engine-boundary test | joined query balanced |
| pending arithmetic branch | joined `result_3=[10,MAX-10]`; 7 iterations | 66/66 sessions, no imbalance |
| checked addition | `TMP_0=[1,MAX]` | 6/6 sessions, no imbalance |
| require | continuation `x=[0,99]`; `REQUIRE` purpose observed | 7/7 sessions, no imbalance |
| assert | continuation `x=[0,99]`; `ASSERT` purpose observed | 7/7 sessions, no imbalance |
| storage load/store | store symbol, load symbol, and returned `x` all equal `42` | 12/12 sessions, no imbalance |
| internal call | `_addTen(5)` and caller result equal `15` | 15/15 sessions, no imbalance |
| fixed-bound loop | 19 iterations; one semantic no-op prevents one rerun | 132/132 sessions, no imbalance |
| symbolic multiplication, 250 ms | tagged TIMEOUT full-range fallback; nonlinear strategy unchanged | 9/9 sessions, no imbalance |
| memory load/store | explicit `NotImplementedError`: assembly/Yul is unsupported | no state was silently approximated |

Every completed probe reports zero active sessions, zero cleanup imbalances, zero duplicate reusable
backend assertions, and zero internal reusable unclassified additions. Multiplication retains the
Stage 2 distinction between a timeout fallback and a proven full range.

## Observable changes and limitations

The pending arithmetic join is intentionally more conservative and order-independent: the joined
result is `[10, MAX_UINT256 - 10]`, and neither branch guard nor checked-success fact survives. The
old result depended on whichever predecessor supplied facts first.

The fixed-bound loop now takes 19 rather than the Stage 2 report's 13 worklist iterations because
convergence observes the complete state instead of only variable-name growth. This is not a claim of
better widening. The widening algorithm, trigger, and back-edge classification remain unchanged and
are deferred to Stage 4.

Linear addition and subtraction carry interval bounds required for the branch example. Nonlinear,
bitwise, division, modulo, exponentiation, and shift abstract transfer remain full-range unless the
existing solver proves a tighter result. Path partitioning, relational facts across a join, memory,
and an explicit may-alias domain remain unsupported.

No snapshot was updated. The focused snapshot invocation is blocked during fixture setup by:

```text
ModuleNotFoundError: No module named 'rich'
```

No dependency was installed and no expectation was accepted. Direct probes and semantic unit tests
cover the changed join behavior.

## Stage 2 confirmation

Joined states pass exact `SemanticStateId.active_fact_ids` validation. All Stage 1 ownership and
Stage 2 query-session tests remain green. Query execution does not mutate joined states, predecessor
states, encodings, property registries, or reusable backend assertions, and session telemetry is
balanced.

## Recommended Stage 4 entry point

Begin Stage 4 at `IntervalAnalysis.apply_widening`, the back-edge branch in
`Forward.apply_transfer_function`, and the engine's current back-edge classification. Introduce a
stable loop-header identity and a generation owner tied to genuine CFG back edges. Store separate
previous and current complete header states, solve each value under its own exact state facts, and
replace stale generation-owned facts when advancing a header generation.

Stage 4 should then test multiple back edges per header, predecessor-order independence at headers,
correct previous/current query materialization, delayed or threshold widening only if explicitly
chosen, and cleanup of obsolete loop-generation facts. It should not weaken the complete Stage 3
join or reuse `QuerySession` as loop state.
