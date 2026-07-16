"""
SMT-based program analysis framework.

Provides solver-agnostic interfaces for symbolic execution.
"""

from .types import SMTVariable, Sort, SortKind, CheckSatResult, SMTTerm
from .solver import SMTSolver
from .strategies.z3_solver import Z3Solver
from .query import (
    BoundStatus,
    FeasibilityResult,
    FeasibilityStatus,
    FunctionEncoding,
    QueryDiagnostics,
    QueryMaterialization,
    QueryPurpose,
    QuerySession,
    RangeInterval,
    RangeResult,
)
from .telemetry import (
    SolverTelemetry,
    get_telemetry,
    enable_telemetry,
    disable_telemetry,
    reset_telemetry,
)

__all__ = [
    "BoundStatus",
    "CheckSatResult",
    "FeasibilityResult",
    "FeasibilityStatus",
    "FunctionEncoding",
    "QueryDiagnostics",
    "QueryMaterialization",
    "QueryPurpose",
    "QuerySession",
    "RangeInterval",
    "RangeResult",
    "SMTSolver",
    "SMTTerm",
    "SMTVariable",
    "SolverTelemetry",
    "Sort",
    "SortKind",
    "Z3Solver",
    "disable_telemetry",
    "enable_telemetry",
    "get_telemetry",
    "reset_telemetry",
]

__version__ = "0.1.0"
