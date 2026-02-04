# Interval Analysis Limitations

## Computed Constants in Non-Linear Operations

When using a computed constant (e.g., `x * (-2)` where `-2` is `TMP = 0 - 2`) in multiplication or division, the variable's range is not narrowed optimally. The result range is correct, but the input variable retains its full type range.

**Cause:** Z3's overflow predicates don't back-propagate through non-linear constraints when both operands are SMT variables.

**Fix:** Detect grounded operands and add explicit bounds.

## Phi Nodes

Phi nodes in SSA form merge values from different control flow paths. Our implementation uses a conservative approach:

1. **If lvalue already tracked** (e.g., from parameter binding during interprocedural analysis) → preserve existing constraints
2. **If rvalues tracked** → create disjunction constraint: `result == v1 OR result == v2 OR ...`
3. **If no rvalues tracked** → create unconstrained variable (full type range)

**Rationale:** In Slither's interprocedural SSA, function entry Phi nodes merge values from ALL call sites. When we bind parameters during call handling, we want those precise bindings preserved rather than widened by the Phi's incoming values from other (potentially unanalyzed) call sites.

**Limitation:** The disjunction constraint `(result == op1 OR result == op2)` doesn't narrow ranges well because the solver finds values satisfying *either* equality. At merge points, Phi results typically show full type range even when operands have precise bounds within their branches.

**Example:**
```solidity
uint256 result;
if (x < 50) {
    result = x + 10;  // result_1 ∈ [10, 59] in true branch
} else {
    result = x - 10;  // result_2 ∈ [40, max-10] in false branch
}
return result;  // result_3 shows [0, max] instead of hull [10, max-10]
```

**Impact:** Branch-specific narrowing works correctly. Only merge points show imprecise ranges.

**Why Query-Time Bound Injection Doesn't Work:**
- Overflow constraints are path-scoped (stored in State, not solver)
- At merge points, path constraints from only one branch are available
- Querying operand bounds without their branch's path constraints yields full type range

**Potential Fixes:**
1. **Disjunctive interval domain**: Track `{[10, 59], [40, max-10]}` directly in domain, collapse to hull when exceeding K disjuncts
2. **Store bounds at definition time**: Compute and cache intervals when operations produce them, before merge
3. **Track pre-merge states**: Query operand bounds from branch-specific states before merging

## Loop Analysis (Widening)

Loops require special handling to guarantee analysis termination. Without intervention, loop iterations could produce ever-increasing bounds that never stabilize.

### Threshold Widening

We use **threshold widening** to ensure termination while preserving precision. Thresholds are collected from the function's numeric literals, bounded by type extremes:

```
thresholds = [type_min, ...constants_from_function..., type_max]
```

For uint256: `[0, ...constants..., 2^256 - 1]`

When a bound grows past a threshold, it jumps to the next threshold. If values don't stabilize, widening eventually reaches the type extremes (guaranteed fixpoint).

### Architecture

The engine and analysis layers are separated:

1. **Engine layer** (`direction.py`): Detects back edges (propagation to `NodeType.IFLOOP`) and calls `analysis.apply_widening()`
2. **Analysis layer** (`IntervalAnalysis`):
   - `prepare_for_function()`: Collects thresholds from function literals
   - `apply_widening()`: Applies domain-specific widening logic
3. **Phi handler** (`phi.py`): At loop headers, creates unconstrained variables

```python
# Engine detects back edge, delegates to analysis
is_back_edge = successor.type == NodeType.IFLOOP
if is_back_edge:
    state_to_propagate = analysis.apply_widening(state_to_propagate, son_state.pre, set())
```

This maintains abstraction: the engine knows *when* to widen (back edges) but delegates *how* to widen to each concrete analysis.

### Selective Widening (Attempted)

The implementation attempts **selective widening**: only widen variables whose bounds actually grew, preserve stable ones. However, this doesn't achieve the desired effect due to SMT architecture limitations.

**Algorithm (in `apply_widening`):**
```
for each variable v:
    current_bounds = query_smt(current_state, v)
    previous_bounds = query_smt(previous_state, v)  # matched by base name

    if current_bounds ⊆ previous_bounds:
        # Stable - keep current variable
        result[v] = current[v]
    else:
        # Grew - widen to unconstrained
        result[v] = create_unconstrained_variable()
```

**Why It Doesn't Work:**

The issue is that phi nodes at loop headers must create **unconstrained** variables:

1. If we constrain phi variables to incoming values (e.g., `i_2 == i_1`), the SMT constraints are permanent
2. When the loop counter increments (`i_3 = i_2 + 1`), the back-edge value can't feed back because `i_2` is stuck at 0
3. This makes loop exits unreachable (the solver finds the path unsatisfiable)

Since phi creates unconstrained variables:
- All loop variables start at `[0, MAX]`
- Selective widening compares `[0, MAX]` to `[0, MAX]` → always stable
- No precision is gained

**Example - stable variable that should stay `[0, 0]`:**
```solidity
function test_constant_increment() public pure returns (uint256) {
    uint256 result = 0;
    for (uint256 i = 0; i < 5; i++) {
        result = result;  // never changes!
    }
    return result;
}
```

**Actual analysis output:**
```
Line 21: result_1 ∈ [0, 0]         # Before loop - precise ✓
Line 22: result_2 ∈ [0, MAX]       # Loop header phi - widened ✗
         i_2 ∈ [5, MAX]            # At exit - narrowed ✓
Line 23: result_2 ∈ [0, MAX]       # In body - still widened ✗
         result_3 ∈ [0, MAX]       # After assignment - widened ✗
Line 25: result_2 ∈ [0, MAX]       # At return - widened ✗ (should be [0, 0])
```

Even though `result = result` never changes the value, the analysis reports `[0, MAX]` because the phi at the loop header creates an unconstrained variable.

**Potential Fixes (require architectural changes):**
1. Track bounds as metadata instead of SMT constraints
2. Use solver push/pop to scope constraints per iteration
3. Use unique SMT variable names per iteration (e.g., `i_2_iter1`, `i_2_iter2`)

### Results

Loop analysis produces **sound but conservative** results:

```solidity
function test_fixed_bound_loop() public pure returns (uint256) {
    uint256 sum = 0;
    for (uint256 i = 0; i < 10; i++) {
        sum += i;
    }
    return sum;
}
```

**Actual analysis output:**
```
Line 10: sum_1 ∈ [0, 0]                    # Before loop - precise
Line 11: i_1 ∈ [0, 0]                      # Loop init - precise
         sum_2 ∈ [0, MAX]                  # Loop header phi - widened
         i_2 ∈ [10, MAX]                   # At exit check - narrowed by i >= 10
Line 12: i_2 ∈ [0, 9]                      # In body - narrowed by i < 10
         sum_3 ∈ [0, MAX]                  # After sum += i - widened
         i_3 ∈ [1, 10]                     # After i++ - narrowed
Line 15: sum_2 ∈ [0, MAX]                  # At return - widened (actual: 45)
         i_2 ∈ [10, MAX]                   # At return - narrowed (actual: 10)
```

**What works:**
- `i_2` in loop body: `[0, 9]` ✓ (correctly narrowed by `i < 10`)
- `i_2` at return: `[10, MAX]` ✓ (correctly narrowed by exit `i >= 10`)

**What doesn't work:**
- `sum_2` everywhere: `[0, MAX]` ✗ (should be `[0, 45]` or at return exactly `45`)

### Trade-offs

| Aspect | Behavior |
|--------|----------|
| **Termination** | Guaranteed - widening forces fixpoint |
| **Soundness** | Maintained - intervals are over-approximations |
| **Precision** | Conservative - loop-modified variables lose bounds |
| **Loop counters** | Narrowed by exit conditions (correct final range) |
| **Accumulators** | Full type range (no symbolic loop summarization) |

### Limitations

1. **No narrowing phase**: Don't recover precision after widening by propagating exit conditions backward
2. **No loop unrolling**: Fixed-bound loops aren't unrolled for precise analysis
3. **No symbolic summarization**: Can't express "sum = 0 + 1 + ... + 9 = 45"
4. **SMT overhead**: Each widening comparison requires SMT solver queries for bounds

## Storage Operations (sstore/sload) - Convex Hull

Multiple writes to the same storage slot produce an OR constraint for sload, but intervals show the convex hull.

```solidity
sstore(0, 42)
sstore(0, 45)
let x := sload(0)  // Shows [42, 45], actual values {42, 45}
```

The range `[42, 45]` includes 43, 44 which aren't possible. This is sound (over-approximation) but imprecise. Single-write cases remain precise.

## Internal Dynamic Calls (Function Pointers)

Internal dynamic calls through function-type variables are always unconstrained.

**Behavior:** All results from `InternalDynamicCall` operations return full type range `[0, max]`.

**Rationale:** Function pointers hold references to functions determined at runtime. The target function is unknown at compile time, so we conservatively return unconstrained results.

**Note:** When function pointers are assigned conditionally across branches:
```solidity
function(uint256) pure returns (uint256) fn;
if (flag) {
    fn = double;
} else {
    fn = identity;
}
uint256 result = fn(x);  // unconstrained
```

This may be related to how branches and phi nodes merge control flow, not the `InternalDynamicCall` handler itself. Needs further investigation.

## Dynamic Array Operations

Dynamic array operations (`push()`, `pop()`, dynamic indexing) are intentionally unconstrained.

**Behavior:** All dynamic array elements and lengths return full type range `[0, max]`.

**Rationale:** Solidity's `push()` compiles to IR that reassigns reference variables:
```
REF_N -> LENGTH array     // read length
TMP = REF_N + 1           // increment
REF_N := TMP              // reassign same reference
REF_M -> array[TMP]       // index element
REF_M := value            // write value
```

Tracking precise values through variable-to-variable reassignments would create circular SMT constraints (since the same variable name maps to the same SMT variable). Instead, we skip variable constraints on reassigned references, yielding safe but imprecise `[0, max]` ranges for lengths.

**What works:**
- Constant writes to array elements: `arr[0] = 42` → `[42, 42]`
- Fixed array reads/writes with constant indices
- Push values: `dynamicArray.push(10)` → element constrained to `[10, 10]`

**What doesn't work:**
- Dynamic array lengths: always `[0, max]`
- State array reads without prior write in same function: `[0, max]`
- Initialized array values (state variable initializers not tracked)

## Supported Operations

- ~~assignment~~
- ~~binary~~
- call
- codesize
- condition
- delete
- event_call
- ~~high_level_call~~
- ~~index~~
- init_array
- ~~internal_call~~
- ~~internal_dynamic_call~~
- ~~length~~
- ~~library_call~~
- low_level_call
- lvalue
- ~~member~~
- new_array
- new_contract
- new_elementary_type
- new_structure
- nop
- operation
- ~~phi~~
- ~~phi_callback~~
- ~~return_operation~~
- send
- ~~solidity_call~~
- transfer
- ~~type_conversion~~
- ~~unary~~
- ~~unpack~~
