# Interval Analysis v2 - Architecture Design

## Overview

Clean reimplementation of interval analysis with minimal initial scope. Only Assignment operation is implemented; all other operations raise `NotImplementedError` to enable incremental development.

## Directory Structure

```
slither/analyses/data_flow/analyses/
├── interval_legacy/          # Archived original
└── interval/                  # New implementation
    ├── __init__.py
    ├── analysis/
    │   ├── __init__.py
    │   ├── analysis.py        # IntervalAnalysis
    │   └── domain.py          # IntervalDomain, DomainVariant
    ├── core/
    │   ├── __init__.py
    │   ├── state.py           # State class
    │   └── tracked_variable.py # TrackedSMTVariable
    └── operations/
        ├── __init__.py
        ├── base.py            # BaseOperationHandler ABC
        ├── registry.py        # OperationHandlerRegistry
        └── assignment.py      # AssignmentHandler
```

## Component Specifications

### 1. TrackedSMTVariable (`core/tracked_variable.py`)

SMT variable wrapper with overflow tracking.

```python
from dataclasses import dataclass
from slither.analyses.data_flow.smt.smt_solver import SMTSolver, SMTTerm

@dataclass
class TrackedSMTVariable:
    """SMT variable with overflow tracking."""

    base: SMTTerm
    overflow_flag: SMTTerm
    overflow_amount: SMTTerm

    @classmethod
    def create(
        cls,
        solver: SMTSolver,
        name: str,
        bit_width: int,
    ) -> "TrackedSMTVariable":
        """Create a new tracked variable with overflow tracking terms."""

    def copy_overflow_from(self, other: "TrackedSMTVariable") -> None:
        """Copy overflow metadata from another tracked variable."""

    def assert_no_overflow(self, solver: SMTSolver) -> None:
        """Assert that this variable has not overflowed."""
```

### 2. State (`core/state.py`)

Minimal state tracking only variables.

```python
from typing import Optional

class State:
    """Tracks variable SMT terms."""

    def __init__(self, variables: dict[str, TrackedSMTVariable] | None = None):
        self._variables: dict[str, TrackedSMTVariable] = variables or {}

    def get_variable(self, name: str) -> Optional[TrackedSMTVariable]:
        """Get tracked variable by name, or None if not tracked."""

    def set_variable(self, name: str, var: TrackedSMTVariable) -> None:
        """Set or update a tracked variable."""

    def variable_names(self) -> set[str]:
        """Return all tracked variable names."""

    def deep_copy(self) -> "State":
        """Create a deep copy of the state."""
```

### 3. IntervalDomain (`analysis/domain.py`)

Implements the `Domain` ABC from the engine.

```python
from enum import Enum
from slither.analyses.data_flow.engine.domain import Domain

class DomainVariant(Enum):
    BOTTOM = "bottom"  # Unreachable code path
    STATE = "state"    # Concrete tracked state
    TOP = "top"        # Unconstrained (no information)

class IntervalDomain(Domain):
    """Interval analysis domain with three-valued lattice."""

    @classmethod
    def bottom(cls) -> "IntervalDomain":
        """Create bottom element (unreachable)."""

    @classmethod
    def top(cls) -> "IntervalDomain":
        """Create top element (unconstrained)."""

    @classmethod
    def with_state(cls, state: State) -> "IntervalDomain":
        """Create domain with concrete state."""

    def join(self, other: "IntervalDomain") -> bool:
        """Lattice join: self := self ⊔ other. Returns True if self changed."""

    def deep_copy(self) -> "IntervalDomain":
        """Create a deep copy of this domain."""
```

### 4. BaseOperationHandler (`operations/base.py`)

```python
from abc import ABC, abstractmethod
from slither.slithir.operations import Operation
from slither.core.cfg.node import Node

class BaseOperationHandler(ABC):
    """Abstract base class for operation handlers."""

    def __init__(self, solver: SMTSolver, analysis: IntervalAnalysis):
        self._solver = solver
        self._analysis = analysis

    @property
    def solver(self) -> SMTSolver:
        return self._solver

    @property
    def analysis(self) -> IntervalAnalysis:
        return self._analysis

    @abstractmethod
    def handle(
        self,
        operation: Operation,
        domain: IntervalDomain,
        node: Node,
    ) -> None:
        """Process operation, modifying domain in-place."""
```

### 5. OperationHandlerRegistry (`operations/registry.py`)

```python
from slither.slithir.operations import Assignment, Operation

class OperationHandlerRegistry:
    """Maps operation types to handlers."""

    def __init__(self, solver: SMTSolver, analysis: IntervalAnalysis):
        self._solver = solver
        self._analysis = analysis
        self._handlers: dict[type[Operation], BaseOperationHandler] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all implemented operation handlers."""

    def get_handler(self, op_type: type[Operation]) -> BaseOperationHandler:
        """
        Get handler for operation type.

        Raises:
            NotImplementedError: If operation type has no registered handler
        """
```

### 6. AssignmentHandler (`operations/assignment.py`)

```python
from slither.slithir.operations import Assignment
from slither.slithir.variables import Constant

class AssignmentHandler(BaseOperationHandler):
    """Handles Assignment operations."""

    def handle(
        self,
        operation: Assignment,
        domain: IntervalDomain,
        node: Node,
    ) -> None:
        """Process assignment, modifying domain in-place."""

    def _resolve_variable_name(self, var) -> str:
        """Extract canonical name from SlithIR variable."""

    def _resolve_variable_type(self, var) -> ElementaryType:
        """Extract Solidity type from variable."""

    def _get_bit_width(self, typ: ElementaryType) -> int:
        """Get bit width for Solidity type."""

    def _handle_constant_assignment(
        self,
        tracked: TrackedSMTVariable,
        const: Constant,
        bit_width: int,
    ) -> None:
        """Handle assignment of constant value."""

    def _handle_variable_assignment(
        self,
        domain: IntervalDomain,
        tracked: TrackedSMTVariable,
        rvalue,
    ) -> None:
        """Handle assignment from another variable."""
```

### 7. IntervalAnalysis (`analysis/analysis.py`)

```python
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward

class IntervalAnalysis(Analysis):
    """Forward interval analysis using SMT-based constraints."""

    def __init__(self, solver: SMTSolver):
        self._solver = solver
        self._direction = Forward()
        self._registry = OperationHandlerRegistry(solver, self)

    def domain(self) -> IntervalDomain:
        """Create initial domain with empty state."""

    def direction(self) -> Direction:
        """Return forward direction."""

    def bottom_value(self) -> IntervalDomain:
        """Return bottom (unreachable) domain."""

    def transfer_function(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: Operation,
    ) -> None:
        """Apply operation to domain state in-place."""

    def _transfer_function_helper(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: Operation,
    ) -> None:
        """
        Handle domain variants before dispatching operation.

        - TOP: return (no information to process)
        - BOTTOM: initialize from function parameters, then dispatch
        - STATE: dispatch operation
        """

    def _initialize_domain_from_bottom(
        self,
        node: Node,
        domain: IntervalDomain,
    ) -> None:
        """Initialize domain state and track function parameters."""

    def _dispatch_operation(
        self,
        op: Operation,
        domain: IntervalDomain,
        node: Node,
    ) -> None:
        """Dispatch operation to appropriate handler."""
```

## Implementation Checklist

- [ ] Rename `interval/` to `interval_legacy/`
- [ ] Create `interval/__init__.py`
- [ ] Create `interval/core/__init__.py`
- [ ] Create `interval/core/tracked_variable.py`
- [ ] Create `interval/core/state.py`
- [ ] Create `interval/analysis/__init__.py`
- [ ] Create `interval/analysis/domain.py`
- [ ] Create `interval/operations/__init__.py`
- [ ] Create `interval/operations/base.py`
- [ ] Create `interval/operations/registry.py`
- [ ] Create `interval/operations/assignment.py`
- [ ] Create `interval/analysis/analysis.py`
- [ ] Update imports in `run_analysis.py` if needed
- [ ] Test with simple assignment-only contract

## Future Operations (add incrementally)

| Priority | Operation | Complexity |
|----------|-----------|------------|
| 1 | Binary (arithmetic) | Medium |
| 2 | TypeConversion | Low |
| 3 | Return | Low |
| 4 | Condition | Medium |
| 5 | Phi | Medium |
| 6 | SolidityCall | High |
| 7 | Index, Member, Length | Medium |
| 8 | HighLevelCall, InternalCall | High |
