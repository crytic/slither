from typing import Optional, Set

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.smt_solver.types import CheckSatResult, SMTTerm, Sort, SortKind
from slither.core.cfg.node import Node
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.variable import SlithIRVariable


class RequireHandler(BaseOperationHandler):
    """Handler for require calls."""

    def handle(self, operation: SolidityCall, domain: IntervalDomain, node: Node) -> None:
        self.logger.debug("Handling require call: {operation}", operation=operation)

        if self.solver is None:
            self.logger.warning("Solver is None, skipping require constraint")
            return

        # Skip if domain is not in STATE variant
        if domain.variant != DomainVariant.STATE:
            self.logger.debug("Domain is not in STATE variant, skipping require")
            return

        # When there is a require call, we should retrieve the boolean condition
        # The first argument to require() is always the boolean condition
        if not (operation.arguments and len(operation.arguments) > 0):
            self.logger.error_and_raise(
                "Require call without arguments at node {node}", ValueError, node=node
            )

        boolean_condition_var = operation.arguments[0]

        # Resolve the variable name (e.g., "TMP_0" or "value|value_0")
        condition_name = IntervalSMTUtils.resolve_variable_name(boolean_condition_var)
        if condition_name is None:
            self.logger.warning(
                "Could not resolve variable name for require condition: {var}",
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

        # Try to extract the underlying comparison constraint (e.g., value >= 10)
        # Pass the node and function context to help with extraction
        derived_constraint = self._resolve_condition_constraint(
            boolean_condition_var, domain, condition_tracked, node
        )

        if derived_constraint is not None:
            # We have a direct comparison constraint (e.g., value >= 10)
            # Check if this constraint is satisfiable with current solver state
            # This will correctly detect that 0 >= 10 is false (UNSAT)
            constraint_to_apply = derived_constraint
            self.logger.debug(
                "Extracted comparison constraint for require condition '{name}': {constraint}",
                name=condition_name,
                constraint=derived_constraint,
            )
        else:
            # Fallback: check if the condition bitvector equals 1 (true)
            # This is less precise but should still work if the condition variable
            # was properly constrained by the comparison handler
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
        self.solver.push()
        self.solver.assert_constraint(constraint)

        sat_result = self.solver.check_sat()
        self.solver.pop()

        self.logger.debug(
            "Checking require condition '{name}' constraint satisfiability: {result}",
            name=condition_name,
            result=sat_result,
        )

        if sat_result == CheckSatResult.UNSAT:
            # Constraint is unsatisfiable with current state - mark path as unreachable
            # For example: if value = 0 and constraint is value >= 10, this is UNSAT
            domain.variant = DomainVariant.TOP
            self.logger.debug(
                "Require condition '{name}' is unsatisfiable, setting domain to TOP (unreachable path)",
                name=condition_name,
            )
            return

        if sat_result == CheckSatResult.UNKNOWN:
            self.logger.warning(
                "Require condition '{name}' satisfiability check returned UNKNOWN",
                name=condition_name,
            )

        # Constraint is satisfiable - add it to the solver permanently
        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Require condition '{name}' applied to solver (result: {result})",
            name=condition_name,
            result=sat_result,
        )

    def _resolve_condition_constraint(
        self,
        boolean_condition_var: SlithIRVariable,
        domain: IntervalDomain,
        condition_tracked: TrackedSMTVariable,
        current_node: Optional[Node] = None,
    ) -> Optional[SMTTerm]:
        """Attempt to derive a concrete comparison constraint for the require argument.

        Returns the actual comparison constraint (e.g., value >= 10) that can be checked
        for satisfiability with the current solver state.
        """
        constraint = self._extract_binary_constraint(
            boolean_condition_var, domain, set(), current_node
        )

        # If we found a comparison constraint, link the condition variable to it
        # This ensures the condition variable reflects the comparison result
        if constraint is not None:
            bitvec_constraint = self._bool_to_bitvec(constraint)
            self.solver.assert_constraint(condition_tracked.term == bitvec_constraint)
        return constraint

    def _extract_binary_constraint(
        self,
        condition_var: SlithIRVariable,
        domain: IntervalDomain,
        visited: Set[SlithIRVariable],
        current_node: Optional[Node] = None,
    ) -> Optional[SMTTerm]:
        """Extract comparison constraints from the IR that produced the boolean variable."""
        if condition_var in visited:
            return None
        visited.add(condition_var)

        # First, try to find a direct comparison on this variable
        direct = self._extract_direct_binary_constraint(condition_var, domain, current_node)
        if direct is not None:
            self.logger.debug(
                "Found direct comparison constraint for {var}",
                var=condition_var,
            )
            return direct

        # If not found, trace through assignments (e.g., condition_1 = TMP_0)
        source_var = self._trace_assignment_source(condition_var, current_node)
        if source_var is not None:
            self.logger.debug(
                "Tracing through assignment from {var} to {source}",
                var=condition_var,
                source=source_var,
            )
            return self._extract_binary_constraint(source_var, domain, visited, current_node)

        self.logger.debug(
            "Could not extract comparison constraint for {var}",
            var=condition_var,
        )
        return None

    def _extract_direct_binary_constraint(
        self,
        condition_var: SlithIRVariable,
        domain: IntervalDomain,
        current_node: Optional[Node] = None,
    ) -> Optional[SMTTerm]:
        """Extract a comparison constraint directly from the node where condition_var is defined.

        Looks for Binary operations (comparisons) where condition_var is the lvalue.
        If condition_var doesn't have a node attribute, searches through the function's nodes.
        """
        # First try to get the node from the variable
        condition_node: Optional[Node] = getattr(condition_var, "node", None)

        # If no node on the variable, search through function nodes
        if condition_node is None and current_node is not None:
            function = getattr(current_node, "function", None)
            if function is not None:
                # Search through all nodes in the function to find where condition_var is used
                for node in function.nodes:
                    operations = list(node.irs) + list(node.irs_ssa)
                    for ir in operations:
                        if isinstance(ir, Binary) and ir.lvalue is condition_var:
                            condition_node = node
                            break
                    if condition_node is not None:
                        break

        if condition_node is None:
            self.logger.debug(
                "No node found for condition variable {var}",
                var=condition_var,
            )
            return None

        operations = list(condition_node.irs) + list(condition_node.irs_ssa)
        for ir in operations:
            if not isinstance(ir, Binary):
                continue
            if ir.lvalue is not condition_var:
                continue
            if ir.type not in {
                BinaryType.GREATER_EQUAL,
                BinaryType.GREATER,
                BinaryType.LESS_EQUAL,
                BinaryType.LESS,
                BinaryType.EQUAL,
                BinaryType.NOT_EQUAL,
            }:
                continue

            self.logger.debug(
                "Found binary comparison operation {op} for {var}",
                op=ir.type,
                var=condition_var,
            )
            return self._build_comparison_constraint(ir, domain)

        return None

    def _trace_assignment_source(
        self, condition_var: SlithIRVariable, current_node: Optional[Node] = None
    ) -> Optional[SlithIRVariable]:
        """Trace through assignments to find the source variable.

        For example: if condition_1 = TMP_0, return TMP_0.
        If condition_var doesn't have a node attribute, searches through the function's nodes.
        """
        # First try to get the node from the variable
        condition_node: Optional[Node] = getattr(condition_var, "node", None)

        # If no node on the variable, search through function nodes
        if condition_node is None and current_node is not None:
            function = getattr(current_node, "function", None)
            if function is not None:
                # Search through all nodes in the function to find where condition_var is assigned
                for node in function.nodes:
                    operations = list(node.irs) + list(node.irs_ssa)
                    for ir in operations:
                        if isinstance(ir, Assignment) and ir.lvalue is condition_var:
                            condition_node = node
                            break
                    if condition_node is not None:
                        break

        if condition_node is None:
            return None

        operations = list(condition_node.irs) + list(condition_node.irs_ssa)
        for ir in operations:
            if isinstance(ir, Assignment) and ir.lvalue is condition_var:
                rvalue = ir.rvalue
                if isinstance(rvalue, SlithIRVariable):
                    self.logger.debug(
                        "Tracing assignment: {lvalue} = {rvalue}",
                        lvalue=condition_var,
                        rvalue=rvalue,
                    )
                    return rvalue
        return None

    def _build_comparison_constraint(
        self, binary_op: Binary, domain: IntervalDomain
    ) -> Optional[SMTTerm]:
        """Construct an SMT constraint for a comparison binary operation."""
        if self.solver is None:
            return None

        left_name = IntervalSMTUtils.resolve_variable_name(binary_op.variable_left)
        if left_name is None:
            return None

        left_tracked = IntervalSMTUtils.get_tracked_variable(domain, left_name)
        if left_tracked is None:
            return None

        left_is_signed = self._is_signed(binary_op.variable_left, left_tracked)
        left_int_term = self._term_to_int(left_tracked.term, left_is_signed)

        right_term = self._resolve_operand_term(binary_op.variable_right, domain)
        if right_term is None:
            return None

        comp_type = binary_op.type
        if comp_type == BinaryType.GREATER_EQUAL:
            return left_int_term >= right_term
        if comp_type == BinaryType.GREATER:
            return left_int_term > right_term
        if comp_type == BinaryType.LESS_EQUAL:
            return left_int_term <= right_term
        if comp_type == BinaryType.LESS:
            return left_int_term < right_term
        if comp_type == BinaryType.EQUAL:
            return left_int_term == right_term
        if comp_type == BinaryType.NOT_EQUAL:
            return left_int_term != right_term

        return None

    def _resolve_operand_term(self, operand, domain: IntervalDomain) -> Optional[SMTTerm]:
        """Convert a binary operand into an SMT term."""
        if self.solver is None:
            return None

        if isinstance(operand, Constant):
            if not isinstance(operand.value, (int, bool)):
                return None
            if isinstance(operand.value, bool):
                sort = self._bool_bitvec_sort()
                value = 1 if operand.value else 0
                return self.solver.create_constant(value, sort)
            value = operand.value
            return self.solver.create_constant(value, Sort(kind=SortKind.INT))

        operand_name = IntervalSMTUtils.resolve_variable_name(operand)
        if operand_name is None:
            return None

        tracked = IntervalSMTUtils.get_tracked_variable(domain, operand_name)
        if tracked is None:
            return None

        is_signed = self._is_signed(operand, tracked)
        return self._term_to_int(tracked.term, is_signed)

    def _term_to_int(self, term: SMTTerm, is_signed: bool) -> SMTTerm:
        if self.solver is None:
            raise RuntimeError("Solver is required for term conversion")
        if is_signed:
            return self.solver.bitvector_to_signed_int(term)
        return self.solver.bitvector_to_int(term)

    def _is_signed(self, var, tracked: TrackedSMTVariable) -> bool:
        solidity_type = IntervalSMTUtils.resolve_elementary_type(getattr(var, "type", None))
        if solidity_type is not None:
            return IntervalSMTUtils.is_signed_type(solidity_type)
        metadata_value = tracked.base.metadata.get("is_signed")
        return bool(metadata_value)

    def _bool_bitvec_sort(self) -> Sort:
        return Sort(kind=SortKind.BITVEC, parameters=[256])

    def _bool_to_bitvec(self, condition: SMTTerm) -> SMTTerm:
        if self.solver is None:
            raise RuntimeError("Solver is required for bool conversion")
        one, zero = self._bool_constants()
        return self.solver.make_ite(condition, one, zero)

    def _bitvec_is_true(self, term: SMTTerm) -> SMTTerm:
        if self.solver is None:
            raise RuntimeError("Solver is required for bool conversion")
        one, _ = self._bool_constants()
        return term == one

    def _bool_constants(self) -> tuple[SMTTerm, SMTTerm]:
        if not hasattr(self, "_bool_one"):
            sort = self._bool_bitvec_sort()
            self._bool_one = self.solver.create_constant(1, sort)
            self._bool_zero = self.solver.create_constant(0, sort)
        return self._bool_one, self._bool_zero
