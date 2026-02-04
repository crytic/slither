# Interval Analysis v2 - Architecture

## Overview

Forward interval analysis using SMT-based constraints for Solidity smart contracts. Implements
threshold-based loop widening, interprocedural analysis, and branch-specific narrowing.

## Directory Structure (31 files)

```
slither/analyses/data_flow/analyses/interval/
├── __init__.py
├── analysis/
│   ├── __init__.py
│   ├── analysis.py              # IntervalAnalysis - main orchestrator
│   └── domain.py                # IntervalDomain - three-valued lattice
├── core/
│   ├── __init__.py
│   ├── state.py                 # State - variable/constraint tracking
│   └── tracked_variable.py      # TrackedSMTVariable - SMT wrapper
└── operations/
    ├── __init__.py
    ├── base.py                  # BaseOperationHandler ABC
    ├── registry.py              # OperationHandlerRegistry
    ├── assignment.py            # AssignmentHandler
    ├── binary/
    │   ├── __init__.py
    │   ├── arithmetic.py        # +, -, *, /, %, **, <<, >>, &, |, ^
    │   └── comparison.py        # <, >, <=, >=, ==, !=, &&, ||
    ├── condition.py             # ConditionHandler (no-op, branching via engine)
    ├── unary.py                 # !, ~ (logical/bitwise not)
    ├── type_conversion.py       # Type widening/narrowing/sign conversion
    ├── phi.py                   # PhiHandler - SSA merge points
    ├── phi_callback.py          # PhiCallbackHandler - state var merge
    ├── return_operation.py      # ReturnHandler
    ├── internal_call.py         # InternalCallHandler
    ├── internal_dynamic_call.py # InternalDynamicCallHandler (function pointers)
    ├── high_level_call.py       # HighLevelCallHandler (external calls)
    ├── library_call.py          # LibraryCallHandler
    ├── solidity_call.py         # SolidityCallHandler (require/assert)
    ├── index.py                 # IndexHandler - array access
    ├── member.py                # MemberHandler - struct fields
    ├── length.py                # LengthHandler - array/bytes length
    ├── unpack.py                # UnpackHandler - tuple extraction
    └── type_utils.py            # Type conversion utilities
```

## Core Components

### IntervalAnalysis (`analysis/analysis.py`)

Main orchestrator implementing forward interval analysis.

**Responsibilities:**
- Operation dispatch via registry
- Threshold collection for loop widening
- Variable declaration handling (initialize to zero)
- Selective threshold-based widening on loop back edges
- Branch narrowing via `apply_condition()`

**Key attributes:**
- `_solver` - SMTSolver instance
- `_registry` - OperationHandlerRegistry
- `_thresholds` - Sorted numeric thresholds for widening
- `_timeout_ms` - SMT query timeout (default 1000ms)

### IntervalDomain (`analysis/domain.py`)

Three-valued lattice: `BOTTOM < STATE < TOP`

| Variant | Meaning |
|---------|---------|
| BOTTOM | Unreachable code path |
| STATE | Concrete tracked state |
| TOP | Unconstrained (no information) |

**Key operations:**
- `join()` - Lattice join (self := self ⊔ other)
- `_merge_states()` - Union variable dictionaries
- `deep_copy()` - Defensive copy for branch analysis

### State (`core/state.py`)

Tracks variables, comparisons, path constraints, and dependencies.

**Internal structures:**
- `_variables: dict[str, TrackedSMTVariable]`
- `_comparisons: dict[str, ComparisonInfo]` - For condition narrowing
- `_path_constraints: list[SMTTerm]` - Branch-specific constraints
- `_dependencies: dict[str, set[str]]` - Cycle detection

### TrackedSMTVariable (`core/tracked_variable.py`)

Lightweight SMT variable wrapper with overflow predicates.

**Attributes:**
- `base` - Underlying SMTVariable
- `no_overflow` - Optional predicate
- `no_underflow` - Optional predicate

## Operation Handlers (17 registered)

| Operation | Handler | Purpose |
|-----------|---------|---------|
| Assignment | AssignmentHandler | Variable assignments |
| Binary | BinaryHandler | Dispatches to Arithmetic/Comparison |
| Condition | ConditionHandler | No-op (engine handles branching) |
| Unary | UnaryHandler | Logical/bitwise not |
| TypeConversion | TypeConversionHandler | Width/sign conversion |
| Phi | PhiHandler | SSA merge points |
| PhiCallback | PhiCallbackHandler | State var merge after external calls |
| Return | ReturnHandler | Constant return tracking |
| InternalCall | InternalCallHandler | Function calls (interprocedural) |
| InternalDynamicCall | InternalDynamicCallHandler | Function pointers (unconstrained) |
| HighLevelCall | HighLevelCallHandler | External calls |
| LibraryCall | LibraryCallHandler | Library function calls |
| SolidityCall | SolidityCallHandler | require()/assert() constraints |
| Index | IndexHandler | Array element access |
| Member | MemberHandler | Struct field access |
| Length | LengthHandler | Array/bytes length |
| Unpack | UnpackHandler | Tuple extraction |

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IntervalAnalysis                                  │
│                                                                             │
│  transfer_function(node, domain, operation)                                 │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────┐                                        │
│  │  OperationHandlerRegistry       │                                        │
│  │  get_handler(operation_type) ───┼──► Handler.handle(op, domain, node)   │
│  └─────────────────────────────────┘                                        │
│                                              │                              │
│                                              ▼                              │
│                                    ┌─────────────────┐                      │
│                                    │  IntervalDomain │                      │
│                                    │   (STATE)       │                      │
│                                    │       │         │                      │
│                                    │       ▼         │                      │
│                                    │   ┌───────┐     │                      │
│                                    │   │ State │     │                      │
│                                    │   └───┬───┘     │                      │
│                                    └───────┼─────────┘                      │
│                                            │                                │
│                                            ▼                                │
│                                 TrackedSMTVariable                          │
│                                    (base, overflow predicates)              │
│                                            │                                │
│                                            ▼                                │
│                                        SMTSolver                            │
│                                    (constraint storage)                     │
└─────────────────────────────────────────────────────────────────────────────┘

Branch Analysis:
                ┌─────────────────┐
                │  apply_condition │
                │  (branch node)   │
                └────────┬────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
   ┌─────────────┐               ┌─────────────┐
   │ True branch │               │ False branch│
   │ +condition  │               │ +¬condition │
   └─────────────┘               └─────────────┘

Loop Widening:
                ┌─────────────────┐
                │  apply_widening  │
                │  (back edge)     │
                └────────┬────────┘
                         │
                         ▼
              Compare old/new bounds
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
     Stable bounds               Bounds grew
     (keep original)            (widen to threshold)
```

## Key Patterns

**SMT Constraint Model:**
- Variables in State have underlying SMTVariable
- Constraints are assertions on solver (permanent)
- Path constraints are branch-specific (separate storage)
- Overflow predicates track arithmetic safety

**Interprocedural Analysis:**
1. Resolve call arguments to SMT terms
2. Bind parameters via prefixed wrappers
3. Recursively process function body
4. Extract and constrain return value

**Widening Strategy:**
1. Extract thresholds from function constants
2. Compare variable bounds between iterations
3. If stable (current ⊆ previous) → keep constraints
4. If grew → widen to next threshold (or full type range)

**Type System:**
- Only ElementaryType tracked (uint*, int*, bool, etc.)
- Complex types trigger element-level tracking
- Bitvector operations via SMT solver
