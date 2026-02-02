# Interval Analysis Limitations

## Computed Constants in Non-Linear Operations

When using a computed constant (e.g., `x * (-2)` where `-2` is `TMP = 0 - 2`) in multiplication or division, the variable's range is not narrowed optimally. The result range is correct, but the input variable retains its full type range.

**Cause:** Z3's overflow predicates don't back-propagate through non-linear constraints when both operands are SMT variables.

**Fix:** Detect grounded operands and add explicit bounds.

## Cross-Branch Constraint Pollution

The SMT solver is shared across all branches during analysis. When the solver accumulates overflow/underflow constraints from one branch (e.g., `ULE(x - 50, x)` asserting x >= 50 to avoid underflow), these constraints affect queries for other branches.

**Example:**
```solidity
if (x > 99) {
    return x - 50;  // Adds constraint: x >= 50 (no underflow)
}
return x + 50;  // Query for x here sees x >= 50 from the OTHER branch
```

**Impact:** In the false branch, x should be in `[0, 99]`, but the solver reports `[50, 99]` due to the constraint from the true branch.

**Cause:** Global solver state doesn't distinguish which constraints belong to which branch.

**Potential Fix:** Track constraint provenance and filter by branch, or use branch-specific solver contexts.

## Phi Nodes

Phi nodes in SSA form merge values from different control flow paths. Our implementation uses a conservative approach:

1. **If lvalue already tracked** (e.g., from parameter binding during interprocedural analysis) → preserve existing constraints
2. **If rvalues tracked** → create disjunction constraint: `result == v1 OR result == v2 OR ...`
3. **If no rvalues tracked** → create unconstrained variable (full type range)

**Rationale:** In Slither's interprocedural SSA, function entry Phi nodes merge values from ALL call sites. When we bind parameters during call handling, we want those precise bindings preserved rather than widened by the Phi's incoming values from other (potentially unanalyzed) call sites.

**Limitation:** We do not perform path-sensitive merging or narrowing based on control flow conditions. The disjunction approach is sound but may be imprecise when many paths converge.

## Supported Operations

- ~~assignment~~
- ~~binary~~
- call
- codesize
- condition
- delete
- event_call
- ~~high_level_call~~
- index
- init_array
- ~~internal_call~~
- internal_dynamic_call
- length
- ~~library_call~~
- low_level_call
- lvalue
- member
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
- unpack
