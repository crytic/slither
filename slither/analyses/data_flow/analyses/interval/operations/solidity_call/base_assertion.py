from typing import Optional

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.operations.binary.comparison import (
    ComparisonBinaryHandler,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.smt_solver.types import CheckSatResult, SMTTerm, Sort, SortKind
from slither.core.cfg.node import Node
from slither.slithir.operations.solidity_call import SolidityCall


class BaseAssertionHandler(BaseOperationHandler):
    """Base handler for require and assert calls."""

    def __init__(self, solver=None, analysis=None, assertion_type: str = "assertion"):
        super().__init__(solver, analysis)
        self.assertion_type = assertion_type

    def handle(self, operation: SolidityCall, domain: IntervalDomain, node: Node) -> None:
        self.logger.debug(
            "Handling {type} call: {operation}", type=self.assertion_type, operation=operation
        )

        if self.solver is None:
            self.logger.warning(
                "Solver is None, skipping {type} constraint", type=self.assertion_type
            )
            return

        # Skip if domain is not in STATE variant
        if domain.variant != DomainVariant.STATE:
            self.logger.debug(
                "Domain is not in STATE variant, skipping {type}", type=self.assertion_type
            )
            return

        # When there is an assertion call, we should retrieve the boolean condition
        # The first argument to require()/assert() is always the boolean condition
        if not (operation.arguments and len(operation.arguments) > 0):
            self.logger.error_and_raise(
                "{type} call without arguments at node {node}",
                ValueError,
                type=self.assertion_type,
                node=node,
            )

        boolean_condition_var = operation.arguments[0]

        # Resolve the variable name (e.g., "TMP_0" or "value|value_0")
        condition_name = IntervalSMTUtils.resolve_variable_name(boolean_condition_var)
        if condition_name is None:
            self.logger.warning(
                "Could not resolve variable name for {type} condition: {var}",
                type=self.assertion_type,
                var=boolean_condition_var,
            )
            return

        # Get the tracked variable from the domain
        condition_tracked = IntervalSMTUtils.get_tracked_variable(domain, condition_name)
        if condition_tracked is None:
            self.logger.warning(
                "Boolean condition variable '{name}' not found in domain state",
                name=condition_name,
            )
            return

        # Try to retrieve the stored Binary operation from our mapping
        stored_op = ComparisonBinaryHandler.get_binary_operation_from_temp(condition_name, domain)
        validated_op = None
        if stored_op is not None:
            validated_op = ComparisonBinaryHandler.validate_constraint_from_temp(
                condition_name, domain
            )

        if validated_op is not None:
            # Build the comparison constraint from the stored operation
            handler = ComparisonBinaryHandler(self.solver)
            constraint = handler.build_comparison_constraint(
                validated_op, domain, node, validated_op
            )
            if constraint is not None:
                # Link the condition variable to the constraint
                bitvec_constraint = self._bool_to_bitvec(constraint)
                self.solver.assert_constraint(condition_tracked.term == bitvec_constraint)
                self.logger.debug(
                    "Extracted comparison constraint for {type} condition '{name}': {constraint}",
                    type=self.assertion_type,
                    name=condition_name,
                    constraint=constraint,
                )
                self._enforce_constraint(constraint, domain, condition_name)
                return

        # Fallback: check if the condition bitvector equals 1 (true)
        constraint_to_apply = self._bitvec_is_true(condition_tracked.term)
        self.logger.debug(
            "Could not extract comparison constraint for '{name}', using bitvector check",
            name=condition_name,
        )
        self._enforce_constraint(constraint_to_apply, domain, condition_name)

    def _enforce_constraint(
        self, constraint: SMTTerm, domain: IntervalDomain, condition_name: str
    ) -> None:
        """Check satisfiability of the constraint and apply it if possible."""
        # Check satisfiability with the constraint added to current solver state
        # This includes all existing constraints (e.g., value = 0)
        # We use push/pop to check without permanently modifying the solver state
        # Note: push/pop preserves all previously asserted constraints, so if value_0 = 0
        # was asserted earlier, it will be included in the satisfiability check
        self.solver.push()
        self.solver.assert_constraint(constraint)

        sat_result = self.solver.check_sat()
        self.solver.pop()

        self.logger.debug(
            "Checking {type} condition '{name}' constraint satisfiability: {result}",
            type=self.assertion_type,
            name=condition_name,
            result=sat_result,
        )

        if sat_result == CheckSatResult.UNSAT:
            # Constraint is unsatisfiable with current state - mark path as unreachable
            # For example: if value = 0 and constraint is value >= 10, this is UNSAT
            domain.variant = DomainVariant.TOP
            self.logger.debug(
                "{type} condition '{name}' is unsatisfiable, setting domain to TOP (unreachable path)",
                type=self.assertion_type,
                name=condition_name,
            )
            return

        if sat_result == CheckSatResult.UNKNOWN:
            self.logger.warning(
                "{type} condition '{name}' satisfiability check returned UNKNOWN",
                type=self.assertion_type,
                name=condition_name,
            )

        # Constraint is satisfiable - add it to the solver permanently
        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "{type} condition '{name}' applied to solver (result: {result})",
            type=self.assertion_type,
            name=condition_name,
            result=sat_result,
        )

    def _bool_bitvec_sort(self) -> Sort:
        return Sort(kind=SortKind.BITVEC, parameters=[1])

    def _bool_to_bitvec(self, condition: SMTTerm) -> SMTTerm:
        if self.solver is None:
            raise RuntimeError("Solver is required for bool conversion")
        one, zero = self._bool_constants()
        return self.solver.make_ite(condition, one, zero)

    def _bitvec_is_true(self, term: SMTTerm) -> SMTTerm:
        """Check if a bitvector term represents 'true' (non-zero)."""
        if self.solver is None:
            raise RuntimeError("Solver is required for bool conversion")
        # Create zero with the same width as the term
        term_width = self.solver.bv_size(term)
        zero = self.solver.create_constant(0, Sort(kind=SortKind.BITVEC, parameters=[term_width]))
        return term != zero

    def _bool_constants(self) -> tuple[SMTTerm, SMTTerm]:
        if not hasattr(self, "_bool_one"):
            sort = self._bool_bitvec_sort()
            self._bool_one = self.solver.create_constant(1, sort)
            self._bool_zero = self.solver.create_constant(0, sort)
        return self._bool_one, self._bool_zero
