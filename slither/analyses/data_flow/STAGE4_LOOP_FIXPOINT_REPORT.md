# Stage 4 Loop Fixpoint Report

## Scope and outcome

Stage 4 replaces destination-node-kind widening with dominator-defined natural-loop fixpoints. Each
loop header now has a stable identity, per-edge input ownership, a generation lifecycle, and one
replaceable generation-fact set. Widening reads the abstract intervals already stored in the
previous and current complete states; it performs no SMT range queries and does not mutate the
Stage 2 function encoding or query-session infrastructure.

The fixed-bound loop reaches its exit with `sum_2 = [0,45]` and `i_2 = [10,10]`. Its analysis phase
creates zero query sessions, compared with the Stage 3 widening baseline of 132 sessions. Four
explicit post-analysis `sum_2` queries create and close 12 isolated sessions.

Stage 1 fact identity, Stage 2 query isolation, Stage 3 complete state joins, public analysis entry
points, `solve_range`, nonlinear solving, property behavior, and the general FIFO worklist topology
remain unchanged.

## Back-edge classification

`LoopStructure.from_function` classifies an edge `source -> destination` as a natural back edge only
when `destination` is in `source.dominators`. This is the standard available CFG certificate that
the destination dominates the edge source. Incoming edges to the same header that do not satisfy
that predicate are entry edges.

There is no `successor.type == NodeType.IFLOOP` fallback. A preheader-to-`IFLOOP` edge initializes
the header and never invokes widening. Edge and loop collections are sorted by numeric node IDs, so
classification does not depend on function-node, predecessor, successor, or worklist arrival order.

The engine's function loop count now uses the same `LoopStructure` rather than a separate DFS-stack
heuristic.

## Loop identities and generations

The stable identities are:

- `LoopHeaderId(EncodingId, header_node_id)` for one header;
- `ControlFlowEdgeId(source_node_id, destination_node_id)` for one incoming edge;
- `LoopVariableId(header_name, entry_names, back_names)` for one static loop phi binding.

SSA entry and back names are classified using their definition nodes: a definition is loop-carried
when the header dominates that definition node. Names are sorted before becoming identity fields.

`LoopHeaderFixpoint` owns:

- the latest complete contribution from every entry edge;
- the latest complete contribution from every back edge;
- the previous complete header input;
- the current complete header input;
- the latest transferred header output and its generation;
- the current generation number;
- exactly one live tuple of generation-owned facts.

Generation zero is the entry approximation. A genuine back-edge update starts the next generation
only if joining its widened result changes the complete `SemanticStateId`. A duplicate or subsumed
input is a semantic no-op and neither advances the generation nor reruns the header.

If another latch arrives while the header is already queued, the tracker recomputes the same pending
generation from its saved previous input and previous output plus the deterministically combined
edge contributions. It does not compare against a stale output as a new generation.

## Widening lifecycle

`LoopWideningContext` carries the header ID, candidate generation, previous complete input, current
complete candidate input, previous transferred output, and static phi bindings. The default
analysis compatibility method remains available, while loop-aware analyses implement
`apply_loop_widening`.

Interval widening follows two paths:

1. A statically certified finite progression uses abstract unrolling for at most 64 generations.
   Certification requires a constant monotone guard, checked arithmetic, and the same non-zero
   constant step for every back alternative of the controlling phi. Once the conservative trip
   bound is reached, an extra recurrence caused only by the non-relational join is rejected.
2. Other loops use threshold widening. Only the bound back-edge SSA names are widened, using the
   previous header-phi interval from the previous output and the candidate back interval from the
   current input. Thresholds are function literals plus the value's signed or unsigned type bounds.

Both paths preserve the remainder of the current complete state, including storage summaries,
dependencies, comparison metadata, explicit path facts, context, overflow metadata, and path
totality. No base-name matching remains.

Loop-header phis are recomputed from their currently active entry/back SSA alternatives. They are
not installed as cyclic immutable equations. Static loop metadata distinguishes an inactive back
alternative during generation zero from a missing active value. A missing active value yields the
full type interval rather than an under-approximation.

## Generation-fact ownership and replacement

Interval widening emits `LOOP_GENERATION`/`RANGE_BOUND` facts with the `LoopHeaderId`, generation,
context, variable name, and abstract interval in their identity. Their payload is the abstract
`NumericInterval`; they are diagnostic ownership records, not backend assertions.

The header tracker replaces its live fact tuple only when a generation changes or a pending
generation expands. It never registers these facts in `FunctionEncoding`, `State`, the property
registry, or the reusable backend. If an attempted generation is a semantic no-op, the previous
generation and facts remain live. Focused tests prove that generation-one IDs are absent after
generation two replaces them.

`SMTSolver.register_loop_generation_fact` continues to reject direct backend registration. This
prevents a caller from bypassing the header owner with permanent assertions.

## Previous and current state handling

The previous and current states are independent deep copies. The interval transformer reads:

- the previous phi value from `LoopWideningContext.previous_output`;
- the current back-edge value from `LoopWideningContext.current_input`.

Focused tests compare their distinct `SemanticStateId` values and the separately retained previous
output ID. Widening no longer calls `solve_range_result`, so there are no widening query sessions in
which one state could accidentally be materialized for both values.

## Telemetry

Opt-in telemetry adds `loop_fixpoints` metrics for:

- headers classified;
- entry- and back-edge propagations;
- generation advances;
- same-generation pending updates;
- semantic no-ops;
- generation-fact replacements;
- current and maximum live generation facts across headers.

The lifetime probe now snapshots analysis-only query-session totals before optional diagnostic range
queries and supports concise summary output. Telemetry remains disabled by default and is not a
semantic input.

## Files and paths changed

- `engine/loop.py`: natural-loop metadata, identities, widening context/result, and header tracker.
- `engine/direction.py`: natural-edge propagation and generation-aware header ownership.
- `engine/analysis.py`: loop-aware compatibility hooks.
- `engine/engine.py`: function preparation and consistent natural-loop counting.
- `analyses/interval/analysis/loop.py`: phi bindings and finite-progression certificates.
- `analyses/interval/analysis/analysis.py`: abstract-only bounded and threshold widening.
- `analyses/interval/operations/phi.py`: active loop-phi interval transfer without cyclic equations.
- `analyses/interval/operations/registry.py`: loop metadata injection for phi transfer.
- `smt_solver/facts.py`: stable `LoopHeaderId` and loop provenance.
- `smt_solver/solver.py`: explicit rejection of solver-owned loop-generation facts.
- `smt_solver/telemetry.py`: generation lifecycle metrics.
- `tests/unit/analyses/data_flow/test_fact_ownership.py`: updated rejection contract for the
  loop-header owner.
- `tests/unit/analyses/data_flow/test_loop_fixpoint.py`: focused Stage 4 behavior tests.
- `tests/e2e/data_flow/interval/contracts/Test_LoopFixpoint.sol`: real multiple-latch and nested loops.
- `tests/e2e/data_flow/interval/solver_lifetime_probe.py`: analysis/query split and concise output.
- `analyses/interval/LIMITATIONS.md`: current loop behavior and remaining limits.

## Focused tests

The Stage 4 tests prove:

1. the preheader edge is not a back edge;
2. the latch edge is detected by dominance in either node-list order;
3. `LoopHeaderId` is stable;
4. generations advance only for a changed complete header approximation;
5. previous input, current input, and previous output retain their respective semantic IDs;
6. only the latest generation-fact IDs remain owned by the tracker;
7. two back edges produce the same complete state in either arrival order;
8. a duplicate back-edge input causes no generation advance or widening call;
9. interval widening preserves storage, dependencies, comparisons, explicit facts, context, and
   path totality while leaving the encoding and query-session count unchanged;
10. all Stage 1-3 unit tests remain green;
11. every explicit range query closes its Stage 2 sessions without persistent assertions.

## Verification results

Completed successfully:

```text
.venv/bin/pytest -q tests/unit/analyses/data_flow/
62 passed

.venv/bin/ruff check <all modified Python files>
All checks passed

.venv/bin/python -m compileall -q <modified data-flow and test paths>
completed successfully

ty check --python .venv <modified Stage 4 core files>
All checks passed

git diff --check
completed successfully
```

All modified engine and interval-analysis functions pass a targeted cyclomatic-complexity limit of
eight. The existing worklist driver and operation telemetry classifier were split into private
helpers without changing queue order, transfer order, counters, or operation categories.

## Direct probes

All probes used Solidity 0.8.20 and opt-in telemetry.

| Scenario | Result | Lifecycle |
|---|---|---|
| fixed bound | 39 iterations; reachable `sum_2=[0,45]`, `i_2=[10,10]` | analysis 0/0 sessions; four explicit ranges 12/12 |
| two back edges | 15/15 nodes reached; 52 iterations; two latch edges, four generations | analysis 0/0 sessions |
| nested loops | 14/14 nodes reached; 44 iterations; two headers | analysis 0/0 sessions |
| branch arithmetic | joined `result_3=[10, MAX_UINT256-10]` | 3/3 explicit-query sessions |
| storage load/store | `x_1=[42,42]` | 3/3 explicit-query sessions |
| internal call | `_addTen(5)` result `TMP_3=[15,15]` | 3/3 explicit-query sessions |
| checked addition | successful result proven `[0,MAX_UINT256]` | 3/3 explicit-query sessions |
| symbolic multiplication, 50 ms | tagged timeout fallback `[0,MAX_UINT256]` | 3/3 sessions, timeout statuses retained |

Every probe ends with zero active sessions, zero cleanup imbalances, zero persistent backend
assertions, zero duplicate reusable assertions, and zero internal unclassified additions. The
nonlinear strategy and timeout tagging are unchanged.

The fixed loop intentionally takes 39 rather than the Stage 3 total of 19 worklist iterations: it
performs ten certified abstract generations instead of widening the accumulator immediately to top.
The solver cost falls from 132 analysis sessions to zero.

## Observable semantic changes

- A loop-entry edge no longer invokes widening merely because its destination is `IFLOOP`.
- Natural back edges to headers of any CFG node kind can be tracked when dominance proves them.
- Loop phi intervals reflect active SSA alternatives instead of starting unconstrained.
- The fixed-bound accumulator remains `[0,45]`; unsupported or ambiguous active phi alternatives
  become full range.
- Multiple latches are retained as separate edge contributions and joined deterministically.
- Widening uses abstract bounds and creates no solver sessions or backend loop assertions.

No join rule, node revisit rule, worklist queue policy, nonlinear solver, property rule, snapshot
expectation, or public query interface was changed. Stage 4 intentionally replaces the old
destination-kind widening trigger and solver-backed bound lookup with the natural-loop lifecycle
and abstract widening described above.

## Snapshot and environment blocker

No snapshot was updated. The interval snapshot suite remains blocked during fixture import because
the existing environment does not provide the undeclared `rich` package:

```text
ModuleNotFoundError: No module named 'rich'
```

No dependency was installed or added. The global `ty` executable was used because `.venv/bin/ty` is
not present; the modified Stage 4 core files pass. Including `smt_solver/telemetry.py` in the same
type-check invocation reaches its pre-existing `rich.table` imports and reports that environment
blocker.

## Remaining limitations

- The finite progression certificate is deliberately narrow: checked constant steps, constant
  monotone guards, and at most 64 conservative generations.
- Different latch steps, symbolic bounds, unchecked wraparound, or non-monotone updates use
  threshold widening and may become full range quickly.
- Generation facts are diagnostic abstract ownership records; query sessions materialize the
  ordinary derived state range facts, not a second loop-fact channel.
- There is no narrowing, relational invariant, path-disjunctive state, or general symbolic loop
  summary.
- The body state produced immediately before a rejected extra recurrence can be wider than the
  converged header and exit state; it is not propagated back into the header.

## Recommended Stage 5 entry point

Stage 5 should begin in the binary abstract transfer, not in loop ownership. Add sound interval
transformers for nonlinear operations when operand intervals are finite, preserving the existing
tagged solver result as an optional refinement. Multiplication should first compute a signedness- and
overflow-aware abstract product interval, then use isolated Stage 2 sessions only when exact solving
is requested and useful. The Stage 4 header tracker can consume those improved abstract values
without any lifecycle change.
