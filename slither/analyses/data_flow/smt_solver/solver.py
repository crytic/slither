"""Abstract SMT solver interface following SMT-LIB 2.0 standard."""

from abc import ABC, abstractmethod

from slither.analyses.data_flow.smt_solver.facts import (
    EncodingId,
    Fact,
    FactOwnerKind,
    FactRegistry,
    SemanticStateId,
    make_compatibility_query_fact,
)
from slither.analyses.data_flow.smt_solver.query import (
    FeasibilityResult,
    FunctionEncoding,
    QueryMaterialization,
    QueryPurpose,
    QuerySession,
    RangeInterval,
    RangeResult,
    empty_state_id,
)
from slither.analyses.data_flow.smt_solver.types import (
    CheckSatResult,
    RangeSolveStatus,
    SMTTerm,
    SMTVariable,
    Sort,
)


class SMTSolver(ABC):
    """
    Abstract SMT solver following SMT-LIB 2.0 standard.

    Reference: https://smt-lib.org/

    Core SMT-LIB commands implemented:
    - (declare-const name sort)
    - (assert constraint)
    - (check-sat)
    - (get-model)
    - (get-value (term1 term2 ...))
    - (push n)
    - (pop n)
    - (reset)

    Extensions for optimization:
    - (maximize term)
    - (minimize term)
    """

    def __init__(self) -> None:
        self.function_encoding: FunctionEncoding[SMTTerm, SMTVariable] = FunctionEncoding()
        self.variables = self.function_encoding.symbols
        self._property_obligations: FactRegistry[SMTTerm] = FactRegistry()
        self._unclassified_additions = 0
        self._scope_depth = 0
        self._active_query_sessions = 0
        # Note: self.assertions removed - was redundant memory leak
        # Use solver.solver.assertions() to get Z3's native assertion list instead

    # ========================================================================
    # Core SMT-LIB 2.0 Commands
    # ========================================================================

    @abstractmethod
    def declare_const(self, name: str, sort: Sort) -> SMTVariable:
        """
        (declare-const name sort)

        Declare a constant with given name and sort.
        Returns an SMTVariable object containing the solver-specific term.
        Raises ValueError if the variable is already declared.
        """
        pass

    @abstractmethod
    def get_or_declare_const(self, name: str, sort: Sort) -> SMTVariable:
        """
        Get an existing constant or declare a new one if it doesn't exist.

        This is useful for worklist algorithms where the same variable
        may be encountered multiple times.
        """
        pass

    @abstractmethod
    def create_constant(self, value: int, sort: Sort) -> SMTTerm:
        """
        Create a constant value term.

        Args:
            value: The integer value
            sort: The sort (type) of the constant

        Returns:
            An SMTTerm representing the constant value
        """
        pass

    @abstractmethod
    def is_bitvector(self, term: SMTTerm) -> bool:
        """Return True if the solver term is a bitvector."""
        pass

    @abstractmethod
    def bitvector_to_int(self, term: SMTTerm) -> SMTTerm:
        """Convert a bitvector term into the solver's integer domain."""
        pass

    @abstractmethod
    def bitvector_to_signed_int(self, term: SMTTerm) -> SMTTerm:
        """Convert a bitvector term into a signed integer representation."""
        pass

    @abstractmethod
    def make_ite(self, condition: SMTTerm, then_term: SMTTerm, else_term: SMTTerm) -> SMTTerm:
        """Create an if-then-else expression."""
        pass

    @abstractmethod
    def Or(self, *terms: SMTTerm) -> SMTTerm:
        """Create a disjunction (OR) of multiple boolean terms."""
        pass

    @abstractmethod
    def And(self, *terms: SMTTerm) -> SMTTerm:
        """Create a conjunction (AND) of multiple boolean terms."""
        pass

    @abstractmethod
    def Not(self, term: SMTTerm) -> SMTTerm:
        """Create a negation (NOT) of a boolean term."""
        pass

    # ========================================================================
    # Bitvector Arithmetic Operations
    # ========================================================================

    @abstractmethod
    def bv_add(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Two's complement addition for bitvectors."""
        pass

    @abstractmethod
    def bv_sub(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Two's complement subtraction for bitvectors."""
        pass

    @abstractmethod
    def bv_mul(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Two's complement multiplication for bitvectors."""
        pass

    @abstractmethod
    def bv_neg(self, term: SMTTerm) -> SMTTerm:
        """Two's complement negation for bitvectors."""
        pass

    @abstractmethod
    def bv_udiv(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned division for bitvectors."""
        pass

    @abstractmethod
    def bv_sdiv(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Signed division for bitvectors."""
        pass

    @abstractmethod
    def bv_urem(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned remainder for bitvectors."""
        pass

    @abstractmethod
    def bv_srem(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Signed remainder for bitvectors (sign follows dividend)."""
        pass

    @abstractmethod
    def bv_shl(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Left shift for bitvectors."""
        pass

    @abstractmethod
    def bv_lshr(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Logical right shift for bitvectors."""
        pass

    @abstractmethod
    def bv_ashr(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Arithmetic right shift for bitvectors (sign-preserving)."""
        pass

    # ========================================================================
    # Bitvector Bitwise Operations
    # ========================================================================

    @abstractmethod
    def bv_and(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Bitwise AND for bitvectors."""
        pass

    @abstractmethod
    def bv_or(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Bitwise OR for bitvectors."""
        pass

    @abstractmethod
    def bv_xor(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Bitwise XOR for bitvectors."""
        pass

    # ========================================================================
    # Bitvector Overflow/Underflow Detection
    # ========================================================================

    @abstractmethod
    def bv_add_no_overflow(self, left: SMTTerm, right: SMTTerm, signed: bool) -> SMTTerm:
        """Returns True if addition does not overflow."""
        pass

    @abstractmethod
    def bv_add_no_underflow(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Returns True if signed addition does not underflow."""
        pass

    @abstractmethod
    def bv_sub_no_overflow(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Returns True if signed subtraction does not overflow."""
        pass

    @abstractmethod
    def bv_sub_no_underflow(self, left: SMTTerm, right: SMTTerm, signed: bool) -> SMTTerm:
        """Returns True if subtraction does not underflow."""
        pass

    @abstractmethod
    def bv_mul_no_overflow(self, left: SMTTerm, right: SMTTerm, signed: bool) -> SMTTerm:
        """Returns True if multiplication does not overflow."""
        pass

    @abstractmethod
    def bv_mul_no_underflow(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Returns True if signed multiplication does not underflow."""
        pass

    @abstractmethod
    def bv_sdiv_no_overflow(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Returns True if signed division does not overflow."""
        pass

    @abstractmethod
    def bv_neg_no_overflow(self, term: SMTTerm) -> SMTTerm:
        """Returns True if negation does not overflow."""
        pass

    @abstractmethod
    def bv_sign_ext(self, term: SMTTerm, extra_bits: int) -> SMTTerm:
        """Sign-extend a bitvector by extra_bits."""
        pass

    @abstractmethod
    def bv_zero_ext(self, term: SMTTerm, extra_bits: int) -> SMTTerm:
        """Zero-extend a bitvector by extra_bits."""
        pass

    @abstractmethod
    def bv_extract(self, term: SMTTerm, high: int, low: int) -> SMTTerm:
        """Extract bits [high:low] from a bitvector."""
        pass

    @abstractmethod
    def bv_ult(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned less-than comparison for bitvectors."""
        pass

    @abstractmethod
    def bv_slt(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Signed less-than comparison for bitvectors."""
        pass

    @abstractmethod
    def bv_ule(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned less-than-or-equal comparison for bitvectors."""
        pass

    @abstractmethod
    def bv_ugt(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned greater-than comparison for bitvectors."""
        pass

    @abstractmethod
    def bv_uge(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned greater-than-or-equal comparison for bitvectors."""
        pass

    @abstractmethod
    def bv_sle(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Signed less-than-or-equal comparison for bitvectors."""
        pass

    @abstractmethod
    def bv_sgt(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Signed greater-than comparison for bitvectors."""
        pass

    @abstractmethod
    def bv_sge(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Signed greater-than-or-equal comparison for bitvectors."""
        pass

    @abstractmethod
    def bv_size(self, term: SMTTerm) -> int:
        """Get the bit-width of a bitvector term."""
        pass

    @abstractmethod
    def bv_concat(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Concatenate two bitvectors."""
        pass

    @abstractmethod
    def bv_not(self, term: SMTTerm) -> SMTTerm:
        """Bitwise NOT for bitvectors."""
        pass

    def assert_constraint(self, constraint: SMTTerm) -> None:
        """Add an unclassified assertion through the guarded compatibility API."""
        self._unclassified_additions += 1
        from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry

        telemetry = get_telemetry()
        if telemetry is not None and telemetry.enabled:
            telemetry.record_unclassified_addition()
        self._add_constraint(constraint)

    @abstractmethod
    def _add_constraint(self, constraint: SMTTerm) -> None:
        """Add a formula after its ownership boundary has been checked."""
        pass

    def register_immutable_fact(self, fact: Fact[SMTTerm]) -> bool:
        """Register an immutable or context equation idempotently."""
        allowed = {
            FactOwnerKind.IMMUTABLE_EQUATION,
            FactOwnerKind.CONTEXT_EQUATION,
        }
        if fact.fact_id.owner not in allowed:
            raise ValueError("Persistent facts must be immutable or context equations")
        added = self.function_encoding.register_fact(fact)
        self._record_fact_registration(fact, duplicate=not added)
        return added

    def bind_function_encoding(self, encoding_id: EncodingId) -> None:
        """Bind the reusable encoding before transfer creates symbols or facts."""
        self.function_encoding.bind(encoding_id)

    def register_loop_generation_fact(self, fact: Fact[SMTTerm]) -> None:
        """Reject loop facts until Stage 2 provides generation-scoped sessions."""
        if fact.fact_id.owner is not FactOwnerKind.LOOP_GENERATION:
            raise ValueError("Loop facts must use the LOOP_GENERATION owner")
        raise NotImplementedError("Loop-generation facts require generation-scoped query sessions")

    def add_query_local_assumption(self, fact: Fact[SMTTerm]) -> None:
        """Add a classified assumption to the current push/pop query frame."""
        if fact.fact_id.owner is not FactOwnerKind.QUERY_LOCAL:
            raise ValueError("Query assumptions must use the QUERY_LOCAL owner")
        if self._scope_depth == 0:
            raise RuntimeError("Query-local assumptions require an active solver scope")
        self._record_fact_registration(fact, duplicate=False)
        self._add_constraint(fact.formula)

    def register_property_obligation(self, fact: Fact[SMTTerm]) -> bool:
        """Record a property obligation without asserting it globally."""
        if fact.fact_id.owner is not FactOwnerKind.PROPERTY_OBLIGATION:
            raise ValueError("Property facts must use the PROPERTY_OBLIGATION owner")
        added = self._property_obligations.register(fact)
        self._record_fact_registration(fact, duplicate=not added)
        return added

    def get_registered_facts(self) -> tuple[Fact[SMTTerm], ...]:
        """Return persistent immutable/context equations."""
        return self.function_encoding.facts()

    def get_property_obligations(self) -> tuple[Fact[SMTTerm], ...]:
        """Return registered property obligations."""
        return self._property_obligations.values()

    @property
    def unclassified_additions(self) -> int:
        """Return guarded compatibility additions observed by this solver."""
        return self._unclassified_additions

    def _clear_ownership_state(self) -> None:
        """Clear ownership registries when the backend is reset."""
        if self._active_query_sessions:
            raise RuntimeError("Cannot reset a solver with active QuerySession instances")
        self.function_encoding.clear()
        self._property_obligations.clear()
        self._unclassified_additions = 0
        self._scope_depth = 0

    @property
    def active_query_sessions(self) -> int:
        """Return the number of live isolated query sessions."""
        return self._active_query_sessions

    def create_query_session(
        self,
        *,
        purpose: QueryPurpose,
        timeout_ms: int,
        state_id: SemanticStateId | None = None,
        state_facts: tuple[Fact[SMTTerm], ...] = (),
        query_facts: tuple[Fact[SMTTerm], ...] = (),
        property_fact: Fact[SMTTerm] | None = None,
        compatibility_constraints: tuple[SMTTerm, ...] = (),
    ) -> QuerySession[SMTTerm]:
        """Create a disposable session from one complete semantic state."""
        materialization, compatibility_count = self._materialize_query(
            purpose=purpose,
            state_id=state_id,
            state_facts=state_facts,
            query_facts=query_facts,
            property_fact=property_fact,
            compatibility_constraints=compatibility_constraints,
        )
        snapshot = self._persistent_query_snapshot()
        self._active_query_sessions += 1

        def cleanup() -> bool:
            self._active_query_sessions -= 1
            counter_balanced = self._active_query_sessions >= 0
            return counter_balanced and self._persistent_query_snapshot() == snapshot

        try:
            return QuerySession(materialization, timeout_ms, compatibility_count, cleanup)
        except Exception:
            self._active_query_sessions -= 1
            raise

    def _materialize_query(
        self,
        *,
        purpose: QueryPurpose,
        state_id: SemanticStateId | None,
        state_facts: tuple[Fact[SMTTerm], ...],
        query_facts: tuple[Fact[SMTTerm], ...],
        property_fact: Fact[SMTTerm] | None,
        compatibility_constraints: tuple[SMTTerm, ...],
    ) -> tuple[QueryMaterialization[SMTTerm], int]:
        """Snapshot encoding, state, and ephemeral inputs without backend mutation."""
        encoding_id = self.function_encoding.encoding_id
        state_id = state_id or empty_state_id(encoding_id)
        property_is_unregistered = property_fact is not None and (
            self._property_obligations.get(property_fact.fact_id) is None
        )
        if property_is_unregistered:
            raise ValueError("Property obligation must be registered before selection")
        compatibility_facts = self._compatibility_query_facts(
            state_id,
            compatibility_constraints,
        )
        materialization = QueryMaterialization(
            encoding_id=encoding_id,
            state_id=state_id,
            purpose=purpose,
            immutable_facts=self.function_encoding.facts(),
            state_facts=state_facts,
            query_facts=(*query_facts, *compatibility_facts),
            property_fact=property_fact,
        )
        return materialization, len(compatibility_facts)

    def _compatibility_query_facts(
        self,
        state_id: SemanticStateId,
        compatibility_constraints: tuple[SMTTerm, ...],
    ) -> tuple[Fact[SMTTerm], ...]:
        """Wrap reusable-backend and raw-call formulas as ephemeral compatibility facts."""
        backend_assertions = tuple(self.get_assertions())
        facts = tuple(
            make_compatibility_query_fact(
                formula,
                "reusable_backend_assertion",
                index,
                state_id.context_id,
            )
            for index, formula in enumerate(backend_assertions)
        )
        offset = len(facts)
        raw_facts = tuple(
            make_compatibility_query_fact(
                formula,
                "solve_range_extra_constraint",
                offset + index,
                state_id.context_id,
            )
            for index, formula in enumerate(compatibility_constraints)
        )
        return (*facts, *raw_facts)

    def _persistent_query_snapshot(self) -> tuple:
        """Capture all persistent ownership surfaces guarded by query cleanup."""
        backend_assertions = tuple(
            assertion.hash() if hasattr(assertion, "hash") else id(assertion)
            for assertion in self.get_assertions()
        )
        return (
            self.function_encoding.fact_ids(),
            self._property_obligations.ids(),
            backend_assertions,
            self._scope_depth,
        )

    def _enter_scope(self, levels: int) -> None:
        """Record backend scope creation for ownership validation."""
        if levels < 0:
            raise ValueError("Solver scope levels cannot be negative")
        self._scope_depth += levels

    def _exit_scope(self, levels: int) -> None:
        """Record backend scope removal for ownership validation."""
        if levels < 0:
            raise ValueError("Solver scope levels cannot be negative")
        if levels > self._scope_depth:
            raise ValueError("Cannot pop more solver scopes than are active")
        self._scope_depth -= levels

    @staticmethod
    def _record_fact_registration(fact: Fact[SMTTerm], duplicate: bool) -> None:
        """Forward one registration attempt to optional telemetry."""
        from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry

        telemetry = get_telemetry()
        if telemetry is not None and telemetry.enabled:
            telemetry.record_fact_registration(fact.fact_id, duplicate)

    @abstractmethod
    def check_sat(self) -> CheckSatResult:
        """
        (check-sat)

        Check satisfiability of current assertions.
        Returns: SAT, UNSAT, or UNKNOWN
        """
        pass

    @abstractmethod
    def check_sat_with_timeout(self, timeout_ms: int) -> CheckSatResult:
        """
        (check-sat) with timeout

        Check satisfiability with a timeout. Returns UNKNOWN if exceeded.
        """
        pass

    @abstractmethod
    def get_model(self) -> dict[str, SMTTerm] | None:
        """
        (get-model)

        Get model (variable assignments) if last check-sat was SAT.
        Returns: Dictionary mapping variable names to their values
        """
        pass

    @abstractmethod
    def get_value(self, terms: list[SMTTerm]) -> dict[SMTTerm, SMTTerm] | None:
        """
        (get-value (term1 term2 ...))

        Get values of specific terms in the current model.
        Returns: Dictionary mapping terms to their values
        """
        pass

    @abstractmethod
    def push(self, levels: int = 1) -> None:
        """
        (push n)

        Push n levels onto the assertion stack.
        Creates a backtracking point.
        """
        pass

    @abstractmethod
    def pop(self, levels: int = 1) -> None:
        """
        (pop n)

        Pop n levels from the assertion stack.
        Backtracks to previous state.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        (reset)

        Reset the solver to initial state.
        Clears all declarations and assertions.
        """
        pass

    # ========================================================================
    # Optimization Extensions (not in core SMT-LIB but common)
    # ========================================================================

    @abstractmethod
    def maximize(self, term: SMTTerm) -> None:
        """
        (maximize term)

        Add objective to maximize the given term.
        Requires optimization-capable solver.
        """
        pass

    @abstractmethod
    def minimize(self, term: SMTTerm) -> None:
        """
        (minimize term)

        Add objective to minimize the given term.
        Requires optimization-capable solver.
        """
        pass

    # ========================================================================
    # Helper Methods (not SMT-LIB commands)
    # ========================================================================

    def get_variable(self, name: str) -> SMTVariable | None:
        """Get a declared variable by name"""
        return self.variables.get(name)

    def list_variables(self) -> list[str]:
        """List all declared variable names"""
        return list(self.variables.keys())

    @abstractmethod
    def get_assertions(self) -> list[SMTTerm]:
        """Get the list of current assertions in the solver."""
        pass

    @abstractmethod
    def is_eq_constraint(self, term: SMTTerm) -> bool:
        """Check if a term is an equality constraint (a == b)."""
        pass

    @abstractmethod
    def get_eq_operands(self, term: SMTTerm) -> tuple | None:
        """Get the two operands of an equality constraint. Returns None if not an equality."""
        pass

    @abstractmethod
    def is_constant_value(self, term: SMTTerm) -> bool:
        """Check if a term is a constant value (not a variable or expression)."""
        pass

    @abstractmethod
    def get_constant_as_long(self, term: SMTTerm) -> int | None:
        """Get the integer value of a constant term. Returns None if not a constant."""
        pass

    @abstractmethod
    def to_smtlib(self) -> str:
        """
        Export current state as SMT-LIB 2.0 format string.
        Useful for debugging or using with other solvers.
        """
        pass

    @abstractmethod
    def is_bool_true(self, term: SMTTerm) -> bool:
        """Check if a boolean term is the constant True."""
        pass

    @abstractmethod
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
        """Check one isolated immutable/state/query/property materialization."""
        pass

    @abstractmethod
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
        """Return independently typed feasibility, lower, and upper outcomes."""
        pass

    @abstractmethod
    def solve_range(
        self,
        term: SMTTerm,
        extra_constraints: list[SMTTerm] | None = None,
        timeout_ms: int = 500,
        signed: bool = False,
    ) -> tuple[RangeSolveStatus, int | None, int | None]:
        """Find minimum and maximum values of a bitvector term.

        Wraps raw extra_constraints as ephemeral compatibility facts and delegates
        to isolated typed feasibility and objective sessions.

        Args:
            term: The bitvector term to optimize.
            extra_constraints: Additional constraints for this query only.
            timeout_ms: Timeout in milliseconds for each optimization.
            signed: If True, optimize using signed interpretation.

        Returns:
            Tuple of (status, min_value, max_value).
            - SUCCESS: Range computed successfully.
            - UNSAT: Constraints unsatisfiable (unreachable path).
            - TIMEOUT/ERROR: Could not compute range.
        """
        pass

    @abstractmethod
    def eval_in_model(self, term: SMTTerm) -> int | None:
        """Evaluate a term in the current model and return its integer value.

        Must be called after a successful check_sat() that returned SAT.

        Returns:
            The integer value of the term, or None if evaluation fails.
        """
        pass
