"""Core types for SMT solver interface."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union

# Import solver-specific types
from z3 import BitVecRef, BoolRef


# Type alias for solver terms - extend this as we add more solvers
SMTTerm = Union[BitVecRef, BoolRef]
# Future: Union[BitVecRef, BoolRef, CVC5Term, YicesTerm, ...]


class SortKind(Enum):
    """SMT-LIB sort kinds"""

    BOOL = "Bool"
    INT = "Int"
    BITVEC = "BitVec"
    ARRAY = "Array"
    REAL = "Real"


class CheckSatResult(Enum):
    """SMT-LIB check-sat results"""

    SAT = "sat"
    UNSAT = "unsat"
    UNKNOWN = "unknown"


@dataclass
class Sort:
    """SMT-LIB sort (type)"""

    kind: SortKind
    parameters: List[int] = field(default_factory=list)  # e.g., [8] for (_ BitVec 8)

    def __str__(self) -> str:
        if self.parameters:
            return f"({self.kind.value} {' '.join(map(str, self.parameters))})"
        return self.kind.value


@dataclass
class SMTVariable:
    """
    Variable that maps to SMT solver terms.

    Attributes:
        name: Variable identifier
        sort: The SMT-LIB sort (type)
        term: Solver-specific term (BitVecRef, BoolRef, etc.)
        metadata: Additional tracking information
    """

    name: str
    sort: Sort
    term: SMTTerm
    metadata: Dict[str, Optional[SMTTerm]] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"SMTVariable(name='{self.name}', sort={self.sort})"
