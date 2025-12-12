"""Z3 solver strategy implementation."""

from typing import Dict, List, Optional

from z3 import (
    BitVec,
    BitVecVal,
    Bool,
    BV2Int,
    Concat,
    Extract,
    If,
    LShR,
    Not as Z3Not,
    Optimize,
    Or,
    SignExt,
    Solver,
    UDiv,
    ULT,
    URem,
    ZeroExt,
    is_bv,
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

    def is_bitvector(self, term: SMTTerm) -> bool:
        return is_bv(term)

    def bitvector_to_int(self, term: SMTTerm) -> SMTTerm:
        return BV2Int(term)

    def bitvector_to_signed_int(self, term: SMTTerm) -> SMTTerm:
        if not self.is_bitvector(term):
            raise TypeError("bitvector_to_signed_int expects a bitvector term")

        width = term.size()
        unsigned = BV2Int(term)
        modulus = 1 << width
        half_range = 1 << (width - 1)
        return If(unsigned >= half_range, unsigned - modulus, unsigned)

    def make_ite(self, condition: SMTTerm, then_term: SMTTerm, else_term: SMTTerm) -> SMTTerm:
        return If(condition, then_term, else_term)

    def Or(self, *terms: SMTTerm) -> SMTTerm:
        """Create a disjunction (OR) of multiple boolean terms."""
        if not terms:
            raise ValueError("Or() requires at least one term")
        if len(terms) == 1:
            return terms[0]
        return Or(*terms)

    def Not(self, term: SMTTerm) -> SMTTerm:
        """Create a negation (NOT) of a boolean term."""
        return Z3Not(term)

    def bv_udiv(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        return UDiv(left, right)

    def bv_urem(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        return URem(left, right)

    def bv_lshr(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        return LShR(left, right)

    def bv_sign_ext(self, term: SMTTerm, extra_bits: int) -> SMTTerm:
        """Sign-extend a bitvector by extra_bits."""
        return SignExt(extra_bits, term)

    def bv_zero_ext(self, term: SMTTerm, extra_bits: int) -> SMTTerm:
        """Zero-extend a bitvector by extra_bits."""
        return ZeroExt(extra_bits, term)

    def bv_extract(self, term: SMTTerm, high: int, low: int) -> SMTTerm:
        """Extract bits [high:low] from a bitvector."""
        return Extract(high, low, term)

    def bv_ult(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned less-than comparison for bitvectors."""
        return ULT(left, right)

    def bv_slt(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Signed less-than comparison for bitvectors."""
        # Convert to signed integers and compare
        left_signed = self.bitvector_to_signed_int(left)
        right_signed = self.bitvector_to_signed_int(right)
        return left_signed < right_signed

    def bv_size(self, term: SMTTerm) -> int:
        """Get the bit-width of a bitvector term."""
        if not self.is_bitvector(term):
            raise TypeError("bv_size expects a bitvector term")
        return term.size()

    def bv_concat(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Concatenate two bitvectors."""
        return Concat(left, right)

    def maximize(self, term: SMTTerm) -> None:
        """Add maximization objective."""
        if not self.use_optimizer:
            raise RuntimeError("maximize() requires use_optimizer=True")
        opt_term = self.bitvector_to_int(term) if self.is_bitvector(term) else term
        self.solver.maximize(opt_term)

    def minimize(self, term: SMTTerm) -> None:
        """Add minimization objective."""
        if not self.use_optimizer:
            raise RuntimeError("minimize() requires use_optimizer=True")
        opt_term = self.bitvector_to_int(term) if self.is_bitvector(term) else term
        self.solver.minimize(opt_term)

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
