# Interval Analysis Limitations

## Computed Constants in Non-Linear Operations

When using a computed constant (e.g., `x * (-2)` where `-2` is `TMP = 0 - 2`) in multiplication or division, the variable's range is not narrowed optimally. The result range is correct, but the input variable retains its full type range.

**Cause:** Z3's overflow predicates don't back-propagate through non-linear constraints when both operands are SMT variables.

**Fix:** Detect grounded operands and add explicit bounds.

## Supported Operations

- ~~assignment~~
- ~~binary~~
- call
- codesize
- condition
- delete
- event_call
- high_level_call
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
- phi
- phi_callback
- ~~return_operation~~
- send
- ~~solidity_call~~
- transfer
- ~~type_conversion~~
- ~~unary~~
- unpack
