# Interval Analysis Limitations

## Multiplication with Computed Constants

When multiplying by a computed constant (e.g., `x * (-2)` where `-2` is `TMP = 0 - 2`), the variable's range is not narrowed optimally. The result range is correct, but the input variable retains its full type range.

**Cause:** Z3's `bv_mul_no_overflow` doesn't back-propagate through non-linear constraints when both operands are SMT variables.

**Fix:** Detect grounded operands and add explicit division-based bounds.
