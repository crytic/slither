"""
SMT-based program analysis framework.

Provides solver-agnostic interfaces for symbolic execution.
"""

from .types import SMTVariable, Sort, SortKind, CheckSatResult, SMTTerm
from .solver import SMTSolver
from .strategies.z3_solver import Z3Solver

__all__ = [
    "SMTVariable",
    "Sort",
    "SortKind",
    "CheckSatResult",
    "SMTTerm",
    "SMTSolver",
    "Z3Solver",
]

__version__ = "0.1.0"

