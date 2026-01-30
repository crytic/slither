"""Z3 solver strategy implementation."""

import os
import time
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
    UGE,
    UGT,
    ULE,
    ULT,
    URem,
    ZeroExt,
    is_bv,
    is_bv_value,
    is_eq,
    is_int_value,
    sat,
    unsat,
)

from slither.analyses.data_flow.smt_solver.solver import SMTSolver
from slither.analyses.data_flow.smt_solver.types import (
    CheckSatResult,
    SMTTerm,
    SMTVariable,
    Sort,
    SortKind,
)

# Constraint dumping for debugging
DUMP_CONSTRAINTS = os.environ.get("DUMP_CONSTRAINTS", "0") == "1"
DUMP_FILE = "/tmp/constraints_dump.txt"
_dump_file_handle = None
_constraint_history: List[str] = []  # Keep track of constraints for dumping


def _get_dump_file():
    global _dump_file_handle
    if _dump_file_handle is None and DUMP_CONSTRAINTS:
        _dump_file_handle = open(DUMP_FILE, "w")
    return _dump_file_handle


def _dump(msg: str):
    if DUMP_CONSTRAINTS:
        f = _get_dump_file()
        if f:
            f.write(msg + "\n")
            f.flush()


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
            # Add timeout to prevent hanging (5 seconds)
            self.solver.set("timeout", 5000)
        self.last_result: Optional[CheckSatResult] = None
        self.model: Optional[object] = None

        # Performance instrumentation
        self.constraint_count = 0
        self.check_call_count = 0
        self.total_check_time = 0.0
        self.last_constraint_log = 0

        # Constraint dumping
        self.dump_enabled = DUMP_CONSTRAINTS
        if self.dump_enabled:
            _dump(f"\n{'='*60}\n[NEW SOLVER] use_optimizer={use_optimizer}\n{'='*60}")

    def declare_const(self, name: str, sort: Sort) -> SMTVariable:
        """Declare a constant in Z3."""
        if name in self.variables:
            raise ValueError(f"Variable '{name}' already declared")
        return self._create_variable(name, sort)

    def get_or_declare_const(self, name: str, sort: Sort) -> SMTVariable:
        """Get an existing constant or declare a new one if it doesn't exist."""
        if name in self.variables:
            return self.variables[name]
        return self._create_variable(name, sort)

    def _create_variable(self, name: str, sort: Sort) -> SMTVariable:
        """Create and register a Z3 variable."""
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
        from z3 import BoolVal, IntVal

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
        # Note: Removed self.assertions.append() - was redundant memory leak
        # Use self.solver.assertions() to get Z3's native assertion list

        # Instrumentation: track constraint count
        self.constraint_count += 1
        if self.constraint_count - self.last_constraint_log >= 500:
            print(f"[Z3] Constraints added: {self.constraint_count}")
            self.last_constraint_log = self.constraint_count

        # Constraint dumping (first 100 constraints only)
        if self.dump_enabled and self.constraint_count <= 100:
            constraint_str = str(constraint)[:200]  # Truncate long constraints
            _dump(f"[Constraint #{self.constraint_count}] {constraint_str}")
            _constraint_history.append(constraint_str)

    def check_sat(self) -> CheckSatResult:
        """Check satisfiability."""
        # Instrumentation: time the check
        self.check_call_count += 1
        start_time = time.time()

        # Dump check_sat call (first 20 only)
        if self.dump_enabled and self.check_call_count <= 20:
            assertions = list(self.solver.assertions())
            _dump(f"\n[CHECK_SAT #{self.check_call_count}] Total assertions: {len(assertions)}")
            if len(assertions) <= 10:
                for i, a in enumerate(assertions):
                    _dump(f"  [{i}] {str(a)[:150]}")
            else:
                _dump("  First 5:")
                for i, a in enumerate(assertions[:5]):
                    _dump(f"  [{i}] {str(a)[:150]}")
                _dump("  Last 5:")
                for i, a in enumerate(assertions[-5:]):
                    _dump(f"  [{len(assertions)-5+i}] {str(a)[:150]}")

        result = self.solver.check()

        elapsed = time.time() - start_time
        self.total_check_time += elapsed

        # Log slow checks
        if elapsed > 1.0:
            print(
                f"[Z3] SLOW check #{self.check_call_count}: {elapsed:.2f}s "
                f"(total: {self.total_check_time:.2f}s, "
                f"constraints: {self.constraint_count})"
            )

        if result == sat:
            self.last_result = CheckSatResult.SAT
            self.model = self.solver.model()
        elif result == unsat:
            self.last_result = CheckSatResult.UNSAT
            self.model = None
        else:
            self.last_result = CheckSatResult.UNKNOWN
            self.model = None

        # Dump result
        if self.dump_enabled and self.check_call_count <= 20:
            _dump(f"  Result: {self.last_result}")

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
            self.solver.set("timeout", 5000)  # Re-apply timeout after reset
        self.variables.clear()
        # Note: self.assertions.clear() removed - list no longer exists
        self.last_result = None
        self.model = None

        # Reset instrumentation counters
        self.constraint_count = 0
        self.check_call_count = 0
        self.total_check_time = 0.0
        self.last_constraint_log = 0

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
        """Signed less-than comparison for bitvectors (pure bitvector, no BV2Int)."""
        # Z3's default < operator on bitvectors is signed comparison
        return left < right

    def bv_ule(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned less-than-or-equal comparison for bitvectors."""
        return ULE(left, right)

    def bv_ugt(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned greater-than comparison for bitvectors."""
        return UGT(left, right)

    def bv_uge(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned greater-than-or-equal comparison for bitvectors."""
        return UGE(left, right)

    def bv_sle(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Signed less-than-or-equal comparison for bitvectors (pure bitvector, no BV2Int)."""
        return left <= right

    def bv_sgt(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Signed greater-than comparison for bitvectors (pure bitvector, no BV2Int)."""
        return left > right

    def bv_sge(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Signed greater-than-or-equal comparison for bitvectors (pure bitvector, no BV2Int)."""
        return left >= right

    def bv_size(self, term: SMTTerm) -> int:
        """Get the bit-width of a bitvector term."""
        if not self.is_bitvector(term):
            raise TypeError("bv_size expects a bitvector term")
        return term.size()

    def bv_concat(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Concatenate two bitvectors."""
        return Concat(left, right)

    def bv_not(self, term: SMTTerm) -> SMTTerm:
        """Bitwise NOT for bitvectors."""
        return ~term

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

        # Assertions (use Z3's native assertions() method)
        for assertion in self.solver.assertions():
            lines.append(f"(assert {assertion})")

        # Commands
        lines.append("(check-sat)")
        lines.append("(get-model)")

        return "\n".join(lines)

    def get_assertions(self) -> list:
        """Get the list of current assertions in the solver."""
        return list(self.solver.assertions())

    def is_eq_constraint(self, term: SMTTerm) -> bool:
        """Check if a term is an equality constraint (a == b)."""
        return is_eq(term)

    def get_eq_operands(self, term: SMTTerm) -> Optional[tuple]:
        """Get the two operands of an equality constraint. Returns None if not an equality."""
        if not is_eq(term):
            return None
        children = term.children()
        if len(children) != 2:
            return None
        return (children[0], children[1])

    def is_constant_value(self, term: SMTTerm) -> bool:
        """Check if a term is a constant value (not a variable or expression)."""
        return is_bv_value(term) or is_int_value(term)

    def get_constant_as_long(self, term: SMTTerm) -> Optional[int]:
        """Get the integer value of a constant term. Returns None if not a constant."""
        if is_bv_value(term) or is_int_value(term):
            return term.as_long()
        return None

    def is_bool_true(self, term: SMTTerm) -> bool:
        """Check if a boolean term is the constant True."""
        from z3 import is_true
        return is_true(term)

    def solve_range(
        self,
        term: SMTTerm,
        extra_constraints: Optional[list] = None,
        timeout_ms: int = 500,
    ) -> tuple[Optional[int], Optional[int]]:
        """Find minimum and maximum values of a bitvector term."""
        from z3 import Optimize, sat

        def _optimize_bound(maximize: bool) -> Optional[int]:
            opt = Optimize()
            opt.set("timeout", timeout_ms)

            # Copy current assertions
            for assertion in self.solver.assertions():
                opt.add(assertion)

            # Add extra constraints
            if extra_constraints:
                for constraint in extra_constraints:
                    opt.add(constraint)

            # Set objective
            if maximize:
                opt.maximize(term)
            else:
                opt.minimize(term)

            # Solve
            result = opt.check()
            if result != sat:
                return None

            model = opt.model()
            if model is None:
                return None

            value = model.eval(term, model_completion=True)
            if hasattr(value, "as_long"):
                return value.as_long()
            return None

        min_val = _optimize_bound(maximize=False)
        max_val = _optimize_bound(maximize=True)
        return min_val, max_val

    def eval_in_model(self, term: SMTTerm) -> Optional[int]:
        """Evaluate a term in the current model and return its integer value."""
        if self.model is None:
            return None
        try:
            value = self.model.eval(term, model_completion=True)
            if hasattr(value, "as_long"):
                return value.as_long()
        except Exception:
            pass
        return None
