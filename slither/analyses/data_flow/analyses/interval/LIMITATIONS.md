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
- internal_dynamic_call
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
