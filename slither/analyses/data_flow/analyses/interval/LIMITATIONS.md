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
