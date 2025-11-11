"""Z3 solver strategy implementation."""

from typing import Dict, List, Optional

from z3 import (
    BitVec,
    Bool,
    BV2Int,
    Optimize,
    Solver,
    sat,
    unsat,
    unknown,
)

from ..types import SMTVariable, Sort, SortKind, CheckSatResult, SMTTerm
from ..solver import SMTSolver


class Z3Solver(SMTSolver):
    """Z3 implementation of SMT solver interface."""

    def __init__(self, use_optimizer: bool = False) -> None:
        """
        Initialize Z3 solver.

        Args:
            use_optimizer: If True, use Z3's Optimize solver for min/max queries.
                          If False, use standard Solver (maximize/minimize will raise error).
        """
        super().__init__()
        self.use_optimizer = use_optimizer
        if use_optimizer:
            self.solver = Optimize()
        else:
            self.solver = Solver()
        self.last_result: Optional[CheckSatResult] = None
        self.model: Optional[object] = None

    def declare_const(self, name: str, sort: Sort) -> SMTVariable:
        """Declare a constant in Z3."""
        if name in self.variables:
            raise ValueError(f"Variable '{name}' already declared")

        # Create Z3 term based on sort
        if sort.kind == SortKind.BOOL:
            term = Bool(name)
        elif sort.kind == SortKind.BITVEC:
            if not sort.parameters or len(sort.parameters) != 1:
                raise ValueError("BitVec sort requires width parameter")
            width = sort.parameters[0]
            term = BitVec(name, width)
        elif sort.kind == SortKind.INT:
            from z3 import Int

            term = Int(name)
        else:
            raise NotImplementedError(f"Sort {sort.kind} not yet implemented for Z3")

        var = SMTVariable(name=name, sort=sort, term=term)
        self.variables[name] = var
        return var

    def create_constant(self, value: int, sort: Sort) -> SMTTerm:
        """Create a constant value term in Z3."""
        from z3 import BitVecVal, BoolVal, IntVal

        if sort.kind == SortKind.BOOL:
            return BoolVal(bool(value))
        elif sort.kind == SortKind.BITVEC:
            if not sort.parameters or len(sort.parameters) != 1:
                raise ValueError("BitVec sort requires width parameter")
            width = sort.parameters[0]
            modulus = 1 << width
            return BitVecVal(value % modulus, width)
        elif sort.kind == SortKind.INT:
            return IntVal(value)
        else:
            raise NotImplementedError(f"Sort {sort.kind} not yet implemented for Z3")

    def assert_constraint(self, constraint: SMTTerm) -> None:
        """Add constraint to Z3 solver."""
        self.solver.add(constraint)
        self.assertions.append(constraint)

    def check_sat(self) -> CheckSatResult:
        """Check satisfiability."""
        result = self.solver.check()

        if result == sat:
            self.last_result = CheckSatResult.SAT
            self.model = self.solver.model()
        elif result == unsat:
            self.last_result = CheckSatResult.UNSAT
            self.model = None
        else:
            self.last_result = CheckSatResult.UNKNOWN
            self.model = None

        return self.last_result

    def get_model(self) -> Optional[Dict[str, SMTTerm]]:
        """Get model from last check-sat."""
        if self.model is None:
            return None

        result: Dict[str, SMTTerm] = {}
        for name, var in self.variables.items():
            result[name] = self.model.eval(var.term, model_completion=True)

        return result

    def get_value(self, terms: List[SMTTerm]) -> Optional[Dict[SMTTerm, SMTTerm]]:
        """Get values of specific terms."""
        if self.model is None:
            return None

        return {term: self.model.eval(term, model_completion=True) for term in terms}

    def push(self, levels: int = 1) -> None:
        """Push assertion stack."""
        for _ in range(levels):
            self.solver.push()

    def pop(self, levels: int = 1) -> None:
        """Pop assertion stack."""
        for _ in range(levels):
            self.solver.pop()

    def reset(self) -> None:
        """Reset solver to initial state."""
        if self.use_optimizer:
            self.solver = Optimize()
        else:
            self.solver = Solver()
        self.variables.clear()
        self.assertions.clear()
        self.last_result = None
        self.model = None

    def maximize(self, term: SMTTerm) -> None:
        """Add maximization objective."""
        if not self.use_optimizer:
            raise RuntimeError("maximize() requires use_optimizer=True")
        self.solver.maximize(
            BV2Int(term) if hasattr(term, "sort") and "BitVec" in str(term.sort()) else term
        )

    def minimize(self, term: SMTTerm) -> None:
        """Add minimization objective."""
        if not self.use_optimizer:
            raise RuntimeError("minimize() requires use_optimizer=True")
        self.solver.minimize(
            BV2Int(term) if hasattr(term, "sort") and "BitVec" in str(term.sort()) else term
        )

    def to_smtlib(self) -> str:
        """Export to SMT-LIB format."""
        lines = []

        # Declarations
        for var in self.variables.values():
            lines.append(f"(declare-const {var.name} {var.sort})")

        # Assertions
        for assertion in self.assertions:
            lines.append(f"(assert {assertion})")

        # Commands
        lines.append("(check-sat)")
        lines.append("(get-model)")

        return "\n".join(lines)
