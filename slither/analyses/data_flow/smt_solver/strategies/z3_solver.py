"""Z3 solver strategy implementation."""

import os
import time

from z3 import (
    UGE,
    UGT,
    ULE,
    ULT,
    BitVec,
    BitVecVal,
    Bool,
    BV2Int,
    BVAddNoOverflow,
    BVAddNoUnderflow,
    BVMulNoOverflow,
    BVMulNoUnderflow,
    BVSDivNoOverflow,
    BVSNegNoOverflow,
    BVSubNoOverflow,
    BVSubNoUnderflow,
    Concat,
    Extract,
    If,
    LShR,
    ModelRef,
    Optimize,
    Or,
    SignExt,
    Solver,
    SRem,
    UDiv,
    URem,
    ZeroExt,
    is_bv,
    is_bv_value,
    is_eq,
    is_int_value,
    sat,
    unsat,
)
from z3 import (
    And as Z3And,
)
from z3 import (
    Not as Z3Not,
)

from slither.analyses.data_flow.smt_solver.solver import SMTSolver
from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry
from slither.analyses.data_flow.smt_solver.facts import Fact, SemanticStateId
from slither.analyses.data_flow.smt_solver.query import (
    BoundStatus,
    FeasibilityResult,
    FeasibilityStatus,
    QueryDiagnostics,
    QueryPurpose,
    QuerySession,
    QuerySessionDiagnostics,
    RangeInterval,
    RangeResult,
)
from slither.analyses.data_flow.smt_solver.types import (
    CheckSatResult,
    RangeSolveStatus,
    SMTTerm,
    SMTVariable,
    Sort,
    SortKind,
)


# Constraint dumping for debugging
DUMP_CONSTRAINTS = os.environ.get("DUMP_CONSTRAINTS", "0") == "1"
DUMP_FILE = "/tmp/constraints_dump.txt"
_dump_file_handle = None
_constraint_history: list[str] = []  # Keep track of constraints for dumping


def _get_dump_file():
    global _dump_file_handle
    if _dump_file_handle is None and DUMP_CONSTRAINTS:
        _dump_file_handle = open(  # noqa: SIM115 -- debug handle persists for the process
            DUMP_FILE, "w"
        )
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
        self.last_result: CheckSatResult | None = None
        self.model: object | None = None
        self.last_range_result: RangeResult | None = None

        # Performance instrumentation
        self.constraint_count = 0
        self.check_call_count = 0
        self.total_check_time = 0.0
        self.last_constraint_log = 0

        # Constraint dumping
        self.dump_enabled = DUMP_CONSTRAINTS
        if self.dump_enabled:
            _dump(f"\n{'=' * 60}\n[NEW SOLVER] use_optimizer={use_optimizer}\n{'=' * 60}")

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

    def _add_constraint(self, constraint: SMTTerm) -> None:
        """Add an ownership-classified constraint to Z3."""
        self.solver.add(constraint)
        # Note: Removed self.assertions.append() - was redundant memory leak
        # Use self.solver.assertions() to get Z3's native assertion list

        # Instrumentation: track constraint count
        self.constraint_count += 1
        if self.constraint_count - self.last_constraint_log >= 500:
            print(f"[Z3] Constraints added: {self.constraint_count}")
            self.last_constraint_log = self.constraint_count

        # Record constraint in telemetry
        self._record_constraint_telemetry(constraint)
        self._record_assertion_lifetime(constraint)

        # Constraint dumping (first 100 constraints only)
        if self.dump_enabled and self.constraint_count <= 100:
            constraint_str = str(constraint)[:200]  # Truncate long constraints
            _dump(f"[Constraint #{self.constraint_count}] {constraint_str}")
            _constraint_history.append(constraint_str)

    def _record_assertion_lifetime(self, constraint: SMTTerm) -> None:
        """Record exact assertion lifetime data when telemetry is enabled."""
        telemetry = get_telemetry()
        if telemetry is None or not telemetry.enabled:
            return
        fingerprint = constraint.sexpr() if hasattr(constraint, "sexpr") else str(constraint)
        telemetry.record_assertion(
            fingerprint,
            len(self.solver.assertions()),
            len(self.variables),
        )

    def _record_constraint_telemetry(self, constraint: SMTTerm) -> None:
        """Classify and record a constraint in telemetry."""
        telemetry = get_telemetry()
        if telemetry is None or not telemetry.enabled:
            return

        # Determine bit width
        bit_width = 256
        if is_bv(constraint):
            bit_width = constraint.size()
        elif hasattr(constraint, "children") and constraint.children():
            for child in constraint.children():
                if is_bv(child):
                    bit_width = child.size()
                    break

        # Classify constraint type based on Z3 expression structure
        constraint_type = self._classify_constraint(constraint)
        telemetry.record_constraint(constraint_type, bit_width)

    def _classify_constraint(self, constraint: SMTTerm) -> str:
        """Classify a constraint into a category."""
        constraint_str = str(constraint.decl()) if hasattr(constraint, "decl") else ""

        # Check for equality
        if is_eq(constraint):
            return "equality"

        # Check for comparison operators
        comparison_ops = ["<", ">", "<=", ">=", "ULT", "ULE", "UGT", "UGE", "SLT", "SLE"]
        if any(op in constraint_str for op in comparison_ops):
            return "inequality"

        # Check for overflow predicates
        overflow_keywords = ["Overflow", "Underflow", "NoOverflow", "NoUnderflow"]
        if any(kw in constraint_str for kw in overflow_keywords):
            return "overflow"

        # Check for arithmetic operations
        arithmetic_ops = ["+", "-", "*", "/", "bvadd", "bvsub", "bvmul", "bvsdiv", "bvudiv"]
        if any(op in constraint_str for op in arithmetic_ops):
            return "arithmetic"

        # Default to path constraint (boolean combinations, etc.)
        return "path"

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
                    _dump(f"  [{len(assertions) - 5 + i}] {str(a)[:150]}")

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

        # Record in telemetry
        self._record_solver_outcome_telemetry(self.last_result, elapsed * 1000)

        # Dump result
        if self.dump_enabled and self.check_call_count <= 20:
            _dump(f"  Result: {self.last_result}")

        return self.last_result

    def _record_solver_outcome_telemetry(self, result: CheckSatResult, elapsed_ms: float) -> None:
        """Record solver outcome in telemetry."""
        telemetry = get_telemetry()
        if telemetry is None or not telemetry.enabled:
            return

        outcome_map = {
            CheckSatResult.SAT: "sat",
            CheckSatResult.UNSAT: "unsat",
            CheckSatResult.UNKNOWN: "unknown",
        }
        outcome = outcome_map.get(result, "unknown")
        telemetry.record_solver_outcome(outcome, elapsed_ms)

    def check_sat_with_timeout(self, timeout_ms: int) -> CheckSatResult:
        """Check satisfiability with a timeout.

        Args:
            timeout_ms: Timeout in milliseconds. Returns UNKNOWN if exceeded.
        """
        self.solver.set("timeout", timeout_ms)
        start_time = time.time()
        result = self._check_sat_internal()  # Use internal to avoid double telemetry
        elapsed = time.time() - start_time
        self.solver.set("timeout", 0)  # Reset to no timeout

        # Record telemetry - distinguish timeout from other UNKNOWN
        elapsed_ms = elapsed * 1000
        if result == CheckSatResult.UNKNOWN and elapsed_ms >= timeout_ms * 0.9:
            # Likely a timeout
            telemetry = get_telemetry()
            if telemetry is not None and telemetry.enabled:
                telemetry.record_solver_outcome("timeout", elapsed_ms)
        else:
            self._record_solver_outcome_telemetry(result, elapsed_ms)

        return result

    def _check_sat_internal(self) -> CheckSatResult:
        """Internal check_sat without telemetry (for use by check_sat_with_timeout)."""
        self.check_call_count += 1
        start_time = time.time()

        result = self.solver.check()

        elapsed = time.time() - start_time
        self.total_check_time += elapsed

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

        return self.last_result

    def get_model(self) -> dict[str, SMTTerm] | None:
        """Get model from last check-sat."""
        if self.model is None:
            return None

        result: dict[str, SMTTerm] = {}
        for name, var in self.variables.items():
            result[name] = self.model.eval(var.term, model_completion=True)

        return result

    def get_value(self, terms: list[SMTTerm]) -> dict[SMTTerm, SMTTerm] | None:
        """Get values of specific terms."""
        if self.model is None:
            return None

        return {term: self.model.eval(term, model_completion=True) for term in terms}

    def push(self, levels: int = 1) -> None:
        """Push assertion stack."""
        self._enter_scope(levels)
        for _ in range(levels):
            self.solver.push()

    def pop(self, levels: int = 1) -> None:
        """Pop assertion stack."""
        self._exit_scope(levels)
        for _ in range(levels):
            self.solver.pop()
        self._record_solver_snapshot()

    def reset(self) -> None:
        """Reset solver to initial state."""
        if self.use_optimizer:
            self.solver = Optimize()
        else:
            self.solver = Solver()
            self.solver.set("timeout", 5000)  # Re-apply timeout after reset
        self.variables.clear()
        self._clear_ownership_state()
        # Note: self.assertions.clear() removed - list no longer exists
        self.last_result = None
        self.model = None

        # Reset instrumentation counters
        self.constraint_count = 0
        self.check_call_count = 0
        self.total_check_time = 0.0
        self.last_constraint_log = 0
        self._record_solver_snapshot()

    def _record_solver_snapshot(self) -> None:
        """Record live solver size when telemetry is enabled."""
        telemetry = get_telemetry()
        if telemetry is None or not telemetry.enabled:
            return
        telemetry.record_solver_snapshot(len(self.solver.assertions()), len(self.variables))

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

    def And(self, *terms: SMTTerm) -> SMTTerm:
        """Create a conjunction (AND) of multiple boolean terms."""
        if not terms:
            raise ValueError("And() requires at least one term")
        if len(terms) == 1:
            return terms[0]
        return Z3And(*terms)

    def Not(self, term: SMTTerm) -> SMTTerm:
        """Create a negation (NOT) of a boolean term."""
        return Z3Not(term)

    # ========================================================================
    # Bitvector Arithmetic Operations
    # ========================================================================

    def bv_add(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Two's complement addition for bitvectors."""
        return left + right

    def bv_sub(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Two's complement subtraction for bitvectors."""
        return left - right

    def bv_mul(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Two's complement multiplication for bitvectors."""
        return left * right

    def bv_neg(self, term: SMTTerm) -> SMTTerm:
        """Two's complement negation for bitvectors."""
        return -term

    def bv_udiv(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned division for bitvectors."""
        return UDiv(left, right)

    def bv_sdiv(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Signed division for bitvectors."""
        return left / right

    def bv_urem(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned remainder for bitvectors."""
        return URem(left, right)

    def bv_srem(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Signed remainder for bitvectors (sign follows dividend)."""
        return SRem(left, right)

    def bv_shl(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Left shift for bitvectors."""
        return left << right

    def bv_lshr(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Logical right shift for bitvectors."""
        return LShR(left, right)

    def bv_ashr(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Arithmetic right shift for bitvectors (sign-preserving)."""
        return left >> right

    # ========================================================================
    # Bitvector Bitwise Operations
    # ========================================================================

    def bv_and(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Bitwise AND for bitvectors."""
        return left & right

    def bv_or(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Bitwise OR for bitvectors."""
        return left | right

    def bv_xor(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Bitwise XOR for bitvectors."""
        return left ^ right

    # ========================================================================
    # Bitvector Overflow/Underflow Detection
    # ========================================================================

    def bv_add_no_overflow(self, left: SMTTerm, right: SMTTerm, signed: bool) -> SMTTerm:
        """Returns True if addition does not overflow."""
        return BVAddNoOverflow(left, right, signed)

    def bv_add_no_underflow(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Returns True if signed addition does not underflow."""
        return BVAddNoUnderflow(left, right)

    def bv_sub_no_overflow(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Returns True if signed subtraction does not overflow."""
        return BVSubNoOverflow(left, right)

    def bv_sub_no_underflow(self, left: SMTTerm, right: SMTTerm, signed: bool) -> SMTTerm:
        """Returns True if subtraction does not underflow."""
        return BVSubNoUnderflow(left, right, signed)

    def bv_mul_no_overflow(self, left: SMTTerm, right: SMTTerm, signed: bool) -> SMTTerm:
        """Returns True if multiplication does not overflow."""
        return BVMulNoOverflow(left, right, signed)

    def bv_mul_no_underflow(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Returns True if signed multiplication does not underflow."""
        return BVMulNoUnderflow(left, right)

    def bv_sdiv_no_overflow(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Returns True if signed division does not overflow."""
        return BVSDivNoOverflow(left, right)

    def bv_neg_no_overflow(self, term: SMTTerm) -> SMTTerm:
        """Returns True if negation does not overflow."""
        return BVSNegNoOverflow(term)

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

        for fact in self.function_encoding.facts():
            lines.append(f"(assert {fact.formula})")

        # Guarded reusable-backend compatibility assertions.
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

    def get_eq_operands(self, term: SMTTerm) -> tuple | None:
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

    def get_constant_as_long(self, term: SMTTerm) -> int | None:
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
        extra_constraints: list | None = None,
        timeout_ms: int = 500,
        signed: bool = False,
    ) -> tuple[RangeSolveStatus, int | None, int | None]:
        """Source-compatible wrapper around the typed range-result API."""
        result = self.solve_range_result(
            term,
            compatibility_constraints=tuple(extra_constraints or ()),
            timeout_ms=timeout_ms,
            signed=signed,
        )
        self.last_range_result = result
        if result.feasibility is FeasibilityStatus.UNSAT:
            return RangeSolveStatus.UNSAT, None, None
        if result.lower_status in {BoundStatus.PROVEN, BoundStatus.ABSTRACT} and (
            result.upper_status in {BoundStatus.PROVEN, BoundStatus.ABSTRACT}
        ):
            return RangeSolveStatus.SUCCESS, result.lower, result.upper
        if self._range_timed_out(result):
            return RangeSolveStatus.TIMEOUT, result.lower, result.upper
        return RangeSolveStatus.ERROR, result.lower, result.upper

    def check_feasibility(
        self,
        *,
        state_id: SemanticStateId | None = None,
        state_facts: tuple[Fact[SMTTerm], ...] = (),
        query_facts: tuple[Fact[SMTTerm], ...] = (),
        purpose: QueryPurpose = QueryPurpose.FEASIBILITY,
        timeout_ms: int = 500,
        property_fact: Fact[SMTTerm] | None = None,
    ) -> FeasibilityResult:
        """Check one state and its ephemeral assumptions in an isolated Solver."""
        session = self.create_query_session(
            purpose=purpose,
            timeout_ms=timeout_ms,
            state_id=state_id,
            state_facts=state_facts,
            query_facts=query_facts,
            property_fact=property_fact,
        )
        status, _reason = self._execute_feasibility_session(session)
        diagnostics = session.diagnostics
        return FeasibilityResult(
            status=status,
            encoding_id=session.materialization.encoding_id,
            state_id=session.materialization.state_id,
            diagnostics=QueryDiagnostics((diagnostics,)),
        )

    def solve_range_result(
        self,
        term: SMTTerm,
        *,
        state_id: SemanticStateId | None = None,
        state_facts: tuple[Fact[SMTTerm], ...] = (),
        query_facts: tuple[Fact[SMTTerm], ...] = (),
        compatibility_constraints: tuple[SMTTerm, ...] = (),
        timeout_ms: int = 500,
        signed: bool = False,
        fallback_range: RangeInterval | None = None,
        abstract_range: RangeInterval | None = None,
    ) -> RangeResult:
        """Solve lower and upper bounds in independent disposable sessions."""
        fallback_range = fallback_range or self._full_type_range(term, signed)
        feasibility = self._range_feasibility(
            state_id=state_id,
            state_facts=state_facts,
            query_facts=query_facts,
            compatibility_constraints=compatibility_constraints,
            timeout_ms=timeout_ms,
        )
        if feasibility.status is FeasibilityStatus.UNSAT:
            return self._unsat_range_result(feasibility)
        if abstract_range is not None:
            return self._abstract_range_result(feasibility, abstract_range)

        objective = self._prepare_objective_term(term, signed)
        lower = self._execute_bound_query(
            term,
            objective,
            maximize=False,
            purpose=QueryPurpose.LOWER_BOUND,
            timeout_ms=timeout_ms,
            state_id=feasibility.state_id,
            state_facts=state_facts,
            query_facts=query_facts,
            compatibility_constraints=compatibility_constraints,
        )
        upper = self._execute_bound_query(
            term,
            objective,
            maximize=True,
            purpose=QueryPurpose.UPPER_BOUND,
            timeout_ms=timeout_ms,
            state_id=feasibility.state_id,
            state_facts=state_facts,
            query_facts=query_facts,
            compatibility_constraints=compatibility_constraints,
        )
        return self._combine_range_outcomes(feasibility, lower, upper, fallback_range)

    def _range_feasibility(
        self,
        *,
        state_id: SemanticStateId | None,
        state_facts: tuple[Fact[SMTTerm], ...],
        query_facts: tuple[Fact[SMTTerm], ...],
        compatibility_constraints: tuple[SMTTerm, ...],
        timeout_ms: int,
    ) -> FeasibilityResult:
        """Establish feasibility once for both objective sessions."""
        session = self.create_query_session(
            purpose=QueryPurpose.FEASIBILITY,
            timeout_ms=min(timeout_ms, 100),
            state_id=state_id,
            state_facts=state_facts,
            query_facts=query_facts,
            compatibility_constraints=compatibility_constraints,
        )
        status, reason = self._execute_feasibility_session(session)
        del reason
        return FeasibilityResult(
            status=status,
            encoding_id=session.materialization.encoding_id,
            state_id=session.materialization.state_id,
            diagnostics=QueryDiagnostics((session.diagnostics,)),
        )

    def _execute_feasibility_session(
        self,
        session: QuerySession[SMTTerm],
    ) -> tuple[FeasibilityStatus, str | None]:
        """Materialize, execute, classify, and always close one Solver session."""
        status = FeasibilityStatus.ERROR
        reason: str | None = None
        try:
            with session:
                solver = self._create_feasibility_backend(session.timeout_ms)
                session.attach_backend(solver)
                solver.add(*(fact.formula for fact in session.materialization.facts))
                started = time.perf_counter()
                result = solver.check()
                elapsed_ms = (time.perf_counter() - started) * 1000
                status, reason = self._classify_feasibility(
                    solver,
                    result,
                    elapsed_ms,
                    session.timeout_ms,
                )
                session.close(feasibility_status=status, reason=reason)
        except Exception as error:  # Z3 exceptions become typed query errors.
            status = FeasibilityStatus.ERROR
            reason = f"{type(error).__name__}: {error}"
            if session.diagnostics.feasibility_status is not FeasibilityStatus.ERROR:
                raise RuntimeError("QuerySession failed to record backend error") from error
        return status, reason

    def _prepare_objective_term(self, term: SMTTerm, signed: bool) -> SMTTerm:
        """Prepare term for optimization, flipping sign bit for signed values."""
        if not signed:
            return term
        width = self.bv_size(term)
        sign_bit_mask = BitVecVal(1 << (width - 1), width)
        return term ^ sign_bit_mask

    def _execute_bound_query(
        self,
        term: SMTTerm,
        objective_term: SMTTerm,
        *,
        maximize: bool,
        purpose: QueryPurpose,
        timeout_ms: int,
        state_id: SemanticStateId,
        state_facts: tuple[Fact[SMTTerm], ...],
        query_facts: tuple[Fact[SMTTerm], ...],
        compatibility_constraints: tuple[SMTTerm, ...],
    ) -> tuple[int | None, BoundStatus, QuerySessionDiagnostics]:
        """Execute one minimum or maximum objective in a fresh Optimize instance."""
        session = self.create_query_session(
            purpose=purpose,
            timeout_ms=timeout_ms,
            state_id=state_id,
            state_facts=state_facts,
            query_facts=query_facts,
            compatibility_constraints=compatibility_constraints,
        )
        value: int | None = None
        status = BoundStatus.ERROR
        reason: str | None = None
        try:
            with session:
                optimizer = self._create_optimizer_backend(timeout_ms)
                session.attach_backend(optimizer)
                optimizer.add(*(fact.formula for fact in session.materialization.facts))
                objective = optimizer.maximize if maximize else optimizer.minimize
                objective(objective_term)
                started = time.perf_counter()
                result = optimizer.check()
                elapsed_ms = (time.perf_counter() - started) * 1000
                status, reason = self._classify_bound(
                    optimizer,
                    result,
                    elapsed_ms,
                    timeout_ms,
                )
                if status is BoundStatus.PROVEN:
                    value = self._bound_model_value(optimizer, term)
                    if value is None:
                        status = BoundStatus.ERROR
                        reason = "optimizer model did not contain a bitvector value"
                session.close(bound_status=status, reason=reason)
        except Exception as error:  # Z3 exceptions become typed query errors.
            status = BoundStatus.ERROR
            reason = f"{type(error).__name__}: {error}"
            if session.diagnostics.bound_status is not BoundStatus.ERROR:
                raise RuntimeError("QuerySession recorded the wrong backend error kind") from error
        return value, status, session.diagnostics

    @staticmethod
    def _create_feasibility_backend(timeout_ms: int) -> Solver:
        """Create one fresh Solver owned only by a feasibility session."""
        solver = Solver()
        solver.set("timeout", timeout_ms)
        return solver

    @staticmethod
    def _create_optimizer_backend(timeout_ms: int) -> Optimize:
        """Create one fresh Optimize instance owned only by one objective session."""
        optimizer = Optimize()
        optimizer.set("timeout", timeout_ms)
        return optimizer

    @staticmethod
    def _classify_feasibility(
        query_solver: object,
        result: object,
        elapsed_ms: float = 0.0,
        timeout_ms: int = 0,
    ) -> tuple[FeasibilityStatus, str | None]:
        """Map a backend check result without collapsing timeout or unknown."""
        if result == sat:
            return FeasibilityStatus.SAT, None
        if result == unsat:
            return FeasibilityStatus.UNSAT, None
        reason = Z3Solver._unknown_reason(query_solver)
        timed_out = Z3Solver._is_timeout_reason(reason) or Z3Solver._used_timeout_budget(
            elapsed_ms,
            timeout_ms,
        )
        status = FeasibilityStatus.TIMEOUT if timed_out else FeasibilityStatus.UNKNOWN
        return status, reason

    @staticmethod
    def _classify_bound(
        query_solver: object,
        result: object,
        elapsed_ms: float = 0.0,
        timeout_ms: int = 0,
    ) -> tuple[BoundStatus, str | None]:
        """Map one optimization result without affecting the other objective."""
        if result == sat:
            return BoundStatus.PROVEN, None
        if result == unsat:
            return BoundStatus.ERROR, "objective became unsatisfiable after SAT feasibility"
        reason = Z3Solver._unknown_reason(query_solver)
        timed_out = Z3Solver._is_timeout_reason(reason) or Z3Solver._used_timeout_budget(
            elapsed_ms,
            timeout_ms,
        )
        status = BoundStatus.TIMEOUT if timed_out else BoundStatus.UNKNOWN
        return status, reason

    @staticmethod
    def _unknown_reason(query_solver: object) -> str:
        """Read an optional backend explanation for an unknown result."""
        reason_unknown = getattr(query_solver, "reason_unknown", None)
        return str(reason_unknown()) if reason_unknown is not None else "unspecified"

    @staticmethod
    def _is_timeout_reason(reason: str) -> bool:
        """Recognize Z3 timeout/cancellation explanations."""
        normalized = reason.lower()
        return "timeout" in normalized or "canceled" in normalized

    @staticmethod
    def _used_timeout_budget(elapsed_ms: float, timeout_ms: int) -> bool:
        """Classify opaque Z3 unknown results that consumed the configured budget."""
        return timeout_ms > 0 and elapsed_ms >= timeout_ms * 0.9

    @staticmethod
    def _bound_model_value(optimizer: Optimize, term: SMTTerm) -> int | None:
        """Read one optimized concrete bitvector value."""
        model: ModelRef = optimizer.model()
        value = model.eval(term, model_completion=True)
        return value.as_long() if is_bv_value(value) else None

    @staticmethod
    def _unsat_range_result(feasibility: FeasibilityResult) -> RangeResult:
        """Return the existing bottom convention after proven UNSAT feasibility."""
        return RangeResult(
            lower=None,
            upper=None,
            feasibility=feasibility.status,
            lower_status=BoundStatus.NOT_ATTEMPTED,
            upper_status=BoundStatus.NOT_ATTEMPTED,
            fallback_range=None,
            encoding_id=feasibility.encoding_id,
            state_id=feasibility.state_id,
            diagnostics=feasibility.diagnostics,
        )

    @staticmethod
    def _abstract_range_result(
        feasibility: FeasibilityResult,
        interval: RangeInterval,
    ) -> RangeResult:
        """Return an explicitly abstract range without creating objectives."""
        return RangeResult(
            lower=interval.lower,
            upper=interval.upper,
            feasibility=feasibility.status,
            lower_status=BoundStatus.ABSTRACT,
            upper_status=BoundStatus.ABSTRACT,
            fallback_range=interval,
            encoding_id=feasibility.encoding_id,
            state_id=feasibility.state_id,
            diagnostics=feasibility.diagnostics,
        )

    @staticmethod
    def _combine_range_outcomes(
        feasibility: FeasibilityResult,
        lower: tuple[int | None, BoundStatus, QuerySessionDiagnostics],
        upper: tuple[int | None, BoundStatus, QuerySessionDiagnostics],
        fallback: RangeInterval,
    ) -> RangeResult:
        """Preserve one proven side and fall back only for a failed objective."""
        lower_value, lower_status, lower_diagnostics = lower
        upper_value, upper_status, upper_diagnostics = upper
        used_fallback = lower_status is not BoundStatus.PROVEN or (
            upper_status is not BoundStatus.PROVEN
        )
        if lower_status is not BoundStatus.PROVEN:
            lower_value = fallback.lower
        if upper_status is not BoundStatus.PROVEN:
            upper_value = fallback.upper
        sessions = (
            *feasibility.diagnostics.sessions,
            lower_diagnostics,
            upper_diagnostics,
        )
        return RangeResult(
            lower=lower_value,
            upper=upper_value,
            feasibility=feasibility.status,
            lower_status=lower_status,
            upper_status=upper_status,
            fallback_range=fallback if used_fallback else None,
            encoding_id=feasibility.encoding_id,
            state_id=feasibility.state_id,
            diagnostics=QueryDiagnostics(sessions),
        )

    def _full_type_range(self, term: SMTTerm, signed: bool) -> RangeInterval:
        """Return the sound type interval used when an objective is inconclusive."""
        if not self.is_bitvector(term):
            raise TypeError("Range solving requires a bitvector term")
        width = self.bv_size(term)
        if signed:
            return RangeInterval(-(1 << (width - 1)), (1 << (width - 1)) - 1)
        return RangeInterval(0, (1 << width) - 1)

    @staticmethod
    def _range_timed_out(result: RangeResult) -> bool:
        """Return whether feasibility or either objective timed out."""
        return result.feasibility is FeasibilityStatus.TIMEOUT or BoundStatus.TIMEOUT in {
            result.lower_status,
            result.upper_status,
        }

    def eval_in_model(self, term: SMTTerm) -> int | None:
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
