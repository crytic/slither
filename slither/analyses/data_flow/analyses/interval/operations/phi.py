"""Handler for Phi operations (SSA merge points)."""

from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.phi import Phi

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
        TrackedSMTVariable,
    )
    from slither.core.cfg.node import Node


class PhiHandler(BaseOperationHandler):
    """Handler for Phi operations (merges values from different branches)."""

    def handle(
        self,
        operation: Optional[Phi],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Handle Phi operation by creating OR constraint for merged values."""
        if operation is None or self.solver is None:
            return

        lvalue_var = self._get_or_create_lvalue_variable(operation.lvalue, domain)
        if lvalue_var is None:
            return

        or_constraints = self._collect_phi_constraints(lvalue_var, operation.rvalues, domain)
        if not or_constraints:
            return

        self._apply_phi_constraint(lvalue_var, or_constraints, operation.rvalues)

    def _get_or_create_lvalue_variable(
        self, lvalue: object, domain: "IntervalDomain"
    ) -> Optional["TrackedSMTVariable"]:
        """Get or create tracked variable for Phi lvalue."""
        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return None

        lvalue_type = IntervalSMTUtils.resolve_elementary_type(getattr(lvalue, "type", None))
        if lvalue_type is None:
            self.logger.debug("Unsupported lvalue type for Phi operation; skipping.")
            return None

        lvalue_var = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if lvalue_var is None:
            lvalue_var = IntervalSMTUtils.create_tracked_variable(
                self.solver, lvalue_name, lvalue_type
            )
            if lvalue_var is None:
                return None
            domain.state.set_range_variable(lvalue_name, lvalue_var)

        return lvalue_var

    def _collect_phi_constraints(
        self,
        lvalue_var: "TrackedSMTVariable",
        rvalues: list[object],
        domain: "IntervalDomain",
    ) -> list[SMTTerm]:
        """Collect equality constraints for each rvalue in Phi operation."""
        or_constraints: list[SMTTerm] = []

        for rvalue in rvalues:
            rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
            if rvalue_name is None:
                continue

            rvalue_var = IntervalSMTUtils.get_tracked_variable(domain, rvalue_name)
            if rvalue_var is None:
                self.logger.debug(
                    "Rvalue '{rvalue_name}' not found in domain for Phi operation",
                    rvalue_name=rvalue_name,
                )
                continue

            constraint = self._create_equality_constraint(lvalue_var, rvalue_var)
            if constraint is not None:
                or_constraints.append(constraint)

        return or_constraints

    def _create_equality_constraint(
        self,
        lvalue_var: "TrackedSMTVariable",
        rvalue_var: "TrackedSMTVariable",
    ) -> Optional[SMTTerm]:
        """Create equality constraint between lvalue and rvalue, handling width mismatches."""
        lvalue_width = self.solver.bv_size(lvalue_var.term)
        rvalue_width = self.solver.bv_size(rvalue_var.term)

        if lvalue_width != rvalue_width:
            rvalue_term = rvalue_var.term
            if rvalue_width < lvalue_width:
                is_signed = bool(rvalue_var.base.metadata.get("is_signed", False))
                rvalue_term = IntervalSMTUtils.extend_to_width(
                    self.solver, rvalue_term, lvalue_width, is_signed
                )
            else:
                rvalue_term = IntervalSMTUtils.truncate_to_width(
                    self.solver, rvalue_term, lvalue_width
                )
            return lvalue_var.term == rvalue_term

        return lvalue_var.term == rvalue_var.term

    def _apply_phi_constraint(
        self,
        lvalue_var: "TrackedSMTVariable",
        or_constraints: list[SMTTerm],
        rvalues: list[object],
    ) -> None:
        """Apply OR constraint to solver."""
        or_constraint: SMTTerm = self.solver.Or(*or_constraints)
        self.solver.assert_constraint(or_constraint)

        lvalue_name = lvalue_var.base.name
        rvalue_names = ", ".join(
            IntervalSMTUtils.resolve_variable_name(rv) or "?" for rv in rvalues
        )
        self.logger.debug(
            "Phi operation: {lvalue_name} = phi({rvalue_names})",
            lvalue_name=lvalue_name,
            rvalue_names=rvalue_names,
        )
