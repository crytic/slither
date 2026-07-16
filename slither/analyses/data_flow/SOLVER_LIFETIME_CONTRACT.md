# Solver Lifetime Diagnosis and Ownership Contract

## Scope and verdict

This report diagnoses the current solver-backed data-flow framework, using the interval
analysis as the failing client. It does not use the obsolete interval implementation as a
behavioral or architectural reference. The measurements were made without changing solver,
worklist, join, widening, or range-solving semantics.

There are two dominant failures, plus one secondary amplifier:

1. Symbolic 256-bit multiplication is intrinsically hard for the current Z3 `Optimize`
   formulation. A two-node function with one permanent equation, three symbols, and one
   state-local fact still exhausts both 10-second optimization timeouts. Solver growth is not
   required to reproduce the timeout.
2. Loop and branch facts do not have a valid owner or replacement lifetime. Joins retain the
   first predecessor's path assumptions, widening queries an old variable under the new
   state's assumptions, and revisits append facts again. This makes results traversal-order
   dependent and makes loop queries operate on stale or duplicated facts.
3. Range solving amplifies both costs. Every range solve constructs one feasibility solver
   and two optimizers, copying all permanent and state-local facts into each. The minimal loop
   performs 16 range solves (48 solver calls), which account for 1,202ms of a 1,243ms analysis.

Permanent duplicate assertions and monotonically live solver state are confirmed defects, but
they are not the dominant cause in either minimal reproduction. Symbol identity is stable, and
the worklist does not explode in the measured loop.

## Exact source trace

The current lifecycle is:

1. `run_analysis.py:337-346` creates one `Z3Solver` per function. `IntervalAnalysis` retains
   that solver for the entire function.
2. `engine/direction.py:76` runs every SSA operation whenever a node is popped. A revisit runs
   the same handler again.
3. Definition handlers add equations through `assert_constraint`, including arithmetic at
   `operations/binary/arithmetic.py:120`, assignment at
   `operations/assignment.py:140,164`, and comparison at
   `operations/binary/comparison.py:71`.
4. `smt_solver/strategies/z3_solver.py:163-165` unconditionally calls `solver.add`. There is no
   formula identity check and no function-analysis push/pop scope, so assertions remain live
   until the per-function solver is discarded.
5. Symbol creation is stable by name. `core/tracked_variable.py:63` delegates to
   `get_or_declare_const`, and `z3_solver.py:119-123` returns the existing symbol for an exact
   name. Revisits therefore duplicate equations over the same terms rather than creating new
   terms.
6. Branch and checked-arithmetic assumptions are stored in `State._path_constraints` through
   `core/state.py:65-71`. `apply_condition` deep-copies a state and adds the branch guard at
   `analysis/analysis.py:310-349`.
7. `IntervalDomain.join` copies the first non-bottom predecessor at
   `analysis/domain.py:65-68`. Every later state-state join calls `_merge_states`, which only
   adds missing variables at `analysis/domain.py:83-93`. It does not join path assumptions,
   comparisons, dependencies, or storage facts.
8. Back-edge propagation calls widening at `engine/direction.py:97-119`. Widening queries both
   the current and previous variables, but `_bounds_are_stable` passes `current_state` to both
   queries at `analysis/analysis.py:453-465`. The previous approximation is therefore tested
   under the current path's assumptions. The widened state then copies every current path fact
   at `analysis/analysis.py:427-431`.
9. `solve_range` at `z3_solver.py:681-707` runs a feasibility check and two bound
   optimizations. The feasibility solver copies all live assertions at `z3_solver.py:709-732`;
   each optimizer copies them again at `z3_solver.py:742-775`. State-local constraints are
   also copied into all three.
10. An optimizer timeout returns `unknown`, `_optimize_bound` returns `None`, and `solve_range`
    reports `RangeSolveStatus.ERROR` rather than `TIMEOUT`. Callers then use full-type fallback
    bounds, hiding the timeout behind a valid-looking result.

There is also a direct scope violation at
`operations/solidity_call/require_assert.py:58-66`: the successful continuation of a
`require` or `assert` is a path-local assumption, but the handler asserts it permanently in
the function solver and checks the accumulated function-wide context.

## Reproductions and measurements

Measurements were taken on 2026-07-15 at commit `c2aea6b11`, with Python 3.14.5, Z3 4.16.0,
Solidity 0.8.20, and arm64 macOS. The opt-in probe is
`tests/e2e/data_flow/interval/solver_lifetime_probe.py`. It enables telemetry explicitly; normal
analysis leaves the new counters disabled.

### Existing symbolic-arithmetic timeout

`tests/e2e/data_flow/interval/contracts/Test_Mul.sol:15-17` is already part of the snapshot
suite. Commit `dfa200174` raised that suite's per-query timeout from 1,000ms to 10,000ms for
complex queries; the current default remains 10,000ms in `interval/conftest.py:61`.

The minimal function is:

```solidity
function test_mul_two_vars(uint256 x, uint256 y) public pure returns (uint256) {
    return x * y;
}
```

The exact probe command was:

```bash
SOLC_VERSION=0.8.20 .venv/bin/python \
  tests/e2e/data_flow/interval/solver_lifetime_probe.py \
  tests/e2e/data_flow/interval/contracts/Test_Mul.sol \
  --function test_mul_two_vars --query-variable '^TMP_1$' --timeout-ms 10000
```

Results:

| Measurement | Value |
|---|---:|
| CFG nodes / worklist pops / revisits | 2 / 2 / 0 |
| Live / unique / duplicate permanent assertions | 1 / 1 / 0 |
| Symbolic variables | 3 |
| State-local facts | 1 (`bvumul_noovfl x_1 y_1`) |
| Feasibility | `unknown`, 129.504ms |
| Minimize | `unknown`, 10,005.577ms |
| Maximize | `unknown`, 10,005.579ms |
| Whole range query | `ERROR`, 20,563.719ms |

The same query with the state-local no-overflow fact omitted has a 0.244ms SAT feasibility
check, but both optimizers still time out at about 1,004ms with a 1,000ms limit. The nonlinear
equation `TMP_1 = x_1 * y_1` alone is sufficient to reproduce optimization failure.

The linear control in `Test_Add.sol:test_add_two_vars` has the same two CFG nodes, one permanent
equation, three symbols, and one state-local checked-arithmetic fact. At a 3,000ms limit it
succeeds in 136.706ms: feasibility 0.444ms, minimize 64.486ms, maximize 69.164ms. Formula
complexity, not lifetime size, distinguishes the cases.

### Minimal loop

The loop reproduction is `Test_ForLoop.sol:test_fixed_bound_loop`. With a 1,000ms query limit:

| Measurement | Value |
|---|---:|
| CFG nodes / worklist pops | 9 / 13 |
| Maximum worklist size | 2 |
| Revisited nodes / maximum visits per node | 4 / 2 |
| Final permanent assertions | 8 live, 6 unique, 2 duplicates |
| Symbolic variables | 8 final and maximum |
| Maximum state-local facts | 3 live, 2 unique in the loop body |
| Widening range solves / solver subqueries | 16 / 48 |
| Assertion copies across subqueries | 432 |
| Solver subquery time / whole analysis | 1,330.388ms / 1,371.542ms |

Every widening subquery copied six permanent assertions and three state-local facts. The two
duplicate permanent formulas were added later, on node revisits:

- `TMP_0 = ite(i_2 < 10, 1, 0)`
- `sum_3 = sum_2 + i_2`

All 48 widening samples saw six live permanent assertions, while the solver ended with eight.
Therefore duplicates are observable leakage but did not cause this loop's query time. The loop
body also ended with the checked-addition fact `sum_2 + i_2 >= sum_2` twice, proving that
state-local lists accumulate on revisit.

The loop cost is query multiplication, not worklist or state explosion: 97.0% of measured
analysis time was inside the 48 solver calls, the queue never exceeded two nodes, no node was
visited more than twice, and the symbol table stopped at eight entries.

### Join-order instability

`Test_Condition_Pending.sol:test_condition_with_arithmetic` has two predecessor states at its
`ENDIF` node:

- true predecessor: `x_1 < 50` and the checked-addition fact;
- false predecessor: `not(x_1 < 50)` and the checked-subtraction fact.

The runtime state at `ENDIF` retained the true predecessor's two facts and discarded both false
predecessor facts. A direct domain reproduction confirms order dependence:

```text
join(left[p], right[not p])  -> [p]
join(right[not p], left[p])  -> [not p]
```

The correct join cannot choose either predecessor's exclusive assumption. It must retain only
facts valid for all incoming states, or represent the alternatives as a guarded disjunction.

## Causal classification

| Hypothesis | Finding | Evidence |
|---|---|---|
| Solver-lifetime leakage | Confirmed, secondary for measured time; semantic for path facts | Permanent `solver.add`, global `require`, monotone live count |
| Duplicate assertions | Confirmed, not dominant in the minimal cases | Loop ends 8/6; all expensive widening queries occurred at 6 live |
| Unstable symbolic identity | Eliminated in these cases | Name interning in source; loop final=max=8 symbols across revisits |
| Stale facts after join/widening | Confirmed; dominant semantic instability | Join-order reproduction; previous bounds queried with current state |
| Worklist or abstract-state explosion | Eliminated in minimal loop | 13 pops, max queue 2, max two visits, eight symbols |
| Optimization overhead | Confirmed multiplier | Three fresh solver contexts and full fact copies per range solve |
| Intrinsic nonlinear solver cost | Dominant symbolic timeout | One nonlinear equation times out; equal-size linear control succeeds |

## Generic ownership contract

The solver backend is an execution mechanism, not the owner of semantic facts. Each fact must
be classified before it can become active. Its owner decides when the fact is materialized into
a solver query.

| Fact class | Owner | Active lifetime | Copy, join, widening, and revisit behavior |
|---|---|---|---|
| Immutable program encodings (SSA definitions and guarded control-flow semantics) | Function or analysis-context encoding | All queries for one function/context | Share on state copy. Join and widening do not change it. Emit once per definition/context; revisits reuse its formula ID. Discard at context end. |
| Path-local assumptions (branch guards, `require`, successful checked arithmetic) | Abstract state on a CFG edge/node | Only states descended from that path | Copy by value or persistent sharing. Join keeps only common/entailed facts or a guarded disjunction, never one arbitrary predecessor. Widen keeps only inductive/common facts. Revisit replaces through lattice join. Discard when the path is merged or killed. |
| Abstract-state facts (interval bounds, taint sets, symbolic store summaries) | Domain state owned by a node/context | Until that node state is superseded | Copy independently. Join with the domain least upper bound. Widen replaces the prior approximation. Revisit compares and supersedes state. Materialize only for a query of that state. |
| Fixpoint-iteration approximations (loop summary, widening generation) | Loop-header iteration context | One approximation generation | Copy only with its owning header state and generation ID. Join through the abstract domain. A new widening generation invalidates the old one; revisits read the current generation. Discard on replacement or function exit. |
| Query-local assumptions (temporary bounds, model blocking, objective setup) | Query session or balanced solver frame | One SAT/optimization call | Never copied into abstract states and never joined or widened. Add after opening a fresh context or `push`; remove with context disposal or `pop`, including on exceptions. |
| Property obligations (negated safety rule, invariant, or postcondition) | Rule/property checker invocation | One property evaluation at one abstract state | Keep the formula as checker data, not copied state. Assert its negation only in the query session. Re-evaluate after joins/widening and on revisits. Remove the active obligation after the query; retain only the result/counterexample artifact. |

The same formula can have different roles. For example, no-overflow is a path-local assumption
when modeling the successful continuation of checked Solidity arithmetic, but the negation of
no-overflow is a property obligation when asking whether unchecked arithmetic can overflow.
The role, not the Z3 expression type, determines ownership.

### Required invariants

1. Every active solver assertion has a fact class, owner/context ID, and generation or query ID.
2. Mutable state and iteration facts have one source of truth outside the backend solver.
   A globally active definition is path-independent or explicitly guarded by reachability.
3. A range/property query is exactly:
   `immutable encoding AND current abstract state AND current path/iteration facts AND`
   `query assumptions AND property obligation`.
4. State copy shares immutable formulas, copies state-owned collections, and copies no active
   query frame or obligation.
5. State join and widening are order-independent at the semantic level. An exclusive
   predecessor fact cannot survive an ordinary join as an unconditional conjunction.
6. Reprocessing an SSA definition is idempotent: it neither creates a new symbol nor adds a
   second immutable equation.
7. Widening replaces the previous generation. Old bounds or guards cannot remain active merely
   because they were once asserted.
8. Query scopes are balanced on success, timeout, `unknown`, and exceptions. The live solver
   fact set after a query equals the set before it.
9. Stable SSA symbols are keyed by analysis context and definition identity. Fresh iteration
   symbols are allowed only for explicit concrete unrolling, not as a substitute for an
   abstract fixpoint state.
10. The backend may cache or share clauses, but those optimizations cannot extend a fact's
    semantic lifetime.

## Minimal regression-test design

The remediation should add structural tests before performance assertions:

1. **Join order:** join states containing `p` and `not p` in both orders. The resulting active
   assumptions and range results must be equivalent, with neither exclusive fact asserted
   unconditionally.
2. **Revisit idempotence:** analyze the existing minimal loop. Permanent assertion additions
   must equal unique immutable encodings, even though node revisits remain greater than zero.
   State-local collections must contain no duplicate formula IDs.
3. **Widen replacement:** widen a loop-header bound twice. A query after the second widening
   must not contain the first generation's approximation, and the previous variable must be
   queried under the previous state rather than the current state's path facts.
4. **Query cleanup:** record the live fact set, run SAT, min, max, timeout, and exception paths,
   then assert that the same fact set remains live. Property obligations must not affect a
   subsequent rule query.
5. **Context identity:** revisit one SSA definition and assert symbol reuse; analyze two call
   contexts and assert that context-sensitive symbols do not collide.
6. **Cost-shape end to end:** keep the existing two-variable addition and multiplication as a
   matched pair. Assert their identical fact counts and query topology. Treat multiplication
   latency as a benchmark with timeout outcome reporting, not a tight wall-clock unit test.

The telemetry unit tests already verify that diagnostics are disabled by default and that the
opt-in path measures duplicate additions, live assertions across push/pop, symbols, copied
facts, and the three range subqueries without changing their result.

## Narrow remediation goal

Implement fact ownership and scoped materialization for the current interval client while
preserving the public `solve_range` interface and the existing worklist topology:

1. Add an immutable, context-namespaced function encoding that emits each SSA equation once.
2. Move successful-continuation facts such as `require`, checked arithmetic, branch guards,
   and iteration approximations into the owning abstract state or iteration context.
3. Make state copy, join, and widening handle all state components explicitly, deduplicate by
   formula identity, and query previous/current bounds under their respective states.
4. Materialize immutable plus state facts into balanced query sessions; never leave query
   assumptions or property obligations in the reusable context.
5. Satisfy the structural regression tests above and show bounded live/copy counts on the loop.

This remediation deliberately does not redesign the worklist, replace `solve_range`, or claim
to make arbitrary nonlinear bit-vector optimization fast. After lifetimes are correct, a
separate performance goal can choose a sound nonlinear fallback, abstract transfer, or total
query budget using uncontaminated measurements. The one-equation multiplication reproduction
shows that lifetime cleanup alone cannot remove that intrinsic solver cost.

## Support for future rule verification

The contract gives rule checking, symbolic execution, invariant inference, and property
verification the same composition boundary. A future checker can reuse the immutable program
encoding, select one abstract/path state, add rule-specific assumptions in a query session, and
assert the negated property obligation. Its result or counterexample is stored by the checker;
none of its active facts leak into another state, loop generation, or rule.

Invariants remain abstract-state or fixpoint facts until proved inductive. Once proved for a
specific program/context they may be promoted deliberately to immutable derived lemmas with
provenance, rather than becoming permanent merely because a solver once saw them. This enables
future verification without building that system as part of the current diagnosis.
