# Rounding Analysis - Overview

I kept working on the rounding analysis. 

**How it works:**
1. Tags variables with rounding directions (UP, DOWN, NEUTRAL, UNKNOWN)
2. Propagates tags through arithmetic operations following mathematical rules
3. Analyzes function calls to track tags across call boundaries
4. Reports conflicts where UP and DOWN mix incorrectly

**Core Rules (from [roundme](https://github.com/crytic/roundme)):**

| Operation | Rule |
|-----------|------|
| A + B | Both operands propagate directly |
| A - B | Subtrahend's direction inverts |
| A * B | Both operands propagate directly |
| A / B | Denominator's direction inverts; defaults to DOWN |

**Tag Sources:**
- Function names containing "up/ceil" → UP, "down/floor" → DOWN
- Division operations → DOWN (as disucessed)
- Interprocedural analysis when names are ambiguous

**Key Features:**
- `--trace UP/DOWN` flag shows provenance chains for debugging
- Detects ceiling division pattern `(a + b - 1) / b`
- Handles branching (if/else) by taking union of possible tags


