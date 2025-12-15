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

        # Always try to propagate struct member fields, even if base Phi is skipped (for struct types)
        self._propagate_struct_members(operation.lvalue, operation.rvalues, domain)

        # If lvalue is not an elementary type (e.g., struct), skip the base Phi constraint
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
        """Apply OR constraint to solver and assert no overflow."""
        or_constraint: SMTTerm = self.solver.Or(*or_constraints)
        self.solver.assert_constraint(or_constraint)

        lvalue_var.assert_no_overflow(self.solver)

        lvalue_name = lvalue_var.base.name
        rvalue_names = ", ".join(
            IntervalSMTUtils.resolve_variable_name(rv) or "?" for rv in rvalues
        )
        self.logger.debug(
            "Phi operation: {lvalue_name} = phi({rvalue_names})",
            lvalue_name=lvalue_name,
            rvalue_names=rvalue_names,
        )

    def _propagate_struct_members(
        self,
        lvalue: object,
        rvalues: list[object],
        domain: "IntervalDomain",
    ) -> None:
        """Propagate struct member fields when merging struct variables through Phi."""
        if self.solver is None:
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return

        # Find all struct member variables for the lvalue (e.g., "user_5.id", "user_5.balance")
        # First, get or create the lvalue member variables
        lvalue_base = lvalue_name.split("|")[0] if "|" in lvalue_name else lvalue_name

        # Find existing struct members from rvalues to determine which members exist
        member_names: set[str] = set()
        all_var_names = list(domain.state.get_range_variables().keys())

        for rvalue in rvalues:
            rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
            if rvalue_name is None:
                continue

            # Find all struct member variables for this rvalue by checking if var starts with "{rvalue_name}."
            rvalue_prefix = f"{rvalue_name}."
            for var_name in all_var_names:
                if var_name.startswith(rvalue_prefix):
                    # Extract member name (everything after the prefix)
                    member_name = var_name[len(rvalue_prefix) :]
                    member_names.add(member_name)
                    self.logger.debug(
                        "Found struct member '{var_name}' matching rvalue '{rvalue}'",
                        var_name=var_name,
                        rvalue=rvalue_name,
                    )

        if not member_names:
            return

        # For each struct member, create a Phi operation
        for member_name in member_names:
            lvalue_member_name = f"{lvalue_name}.{member_name}"

            # Get or create lvalue member variable
            lvalue_member_var = IntervalSMTUtils.get_tracked_variable(domain, lvalue_member_name)
            if lvalue_member_var is None:
                # Try to infer type from rvalue members
                member_type: Optional[ElementaryType] = None
                for rvalue in rvalues:
                    rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
                    if rvalue_name is None:
                        continue
                    rvalue_member_name = f"{rvalue_name}.{member_name}"
                    rvalue_member_var = IntervalSMTUtils.get_tracked_variable(
                        domain, rvalue_member_name
                    )
                    if rvalue_member_var is not None:
                        # Use the same type as the rvalue member
                        if hasattr(rvalue_member_var.base, "metadata"):
                            type_str = rvalue_member_var.base.metadata.get("solidity_type")
                            if type_str:
                                from slither.core.solidity_types.elementary_type import (
                                    ElementaryType,
                                )

                                member_type = ElementaryType(type_str)
                                break

                if member_type is None:
                    continue

                lvalue_member_var = IntervalSMTUtils.create_tracked_variable(
                    self.solver, lvalue_member_name, member_type
                )
                if lvalue_member_var is None:
                    continue
                domain.state.set_range_variable(lvalue_member_name, lvalue_member_var)
                lvalue_member_var.assert_no_overflow(self.solver)

            # Collect equality constraints for each rvalue member
            or_constraints: list[SMTTerm] = []
            for rvalue in rvalues:
                rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
                if rvalue_name is None:
                    continue

                rvalue_member_name = f"{rvalue_name}.{member_name}"
                rvalue_member_var = IntervalSMTUtils.get_tracked_variable(
                    domain, rvalue_member_name
                )

                # Also try with base name in case of SSA version differences
                if rvalue_member_var is None:
                    rvalue_base = rvalue_name.split("|")[0] if "|" in rvalue_name else rvalue_name
                    alt_rvalue_member_name = f"{rvalue_base}.{member_name}"
                    rvalue_member_var = IntervalSMTUtils.get_tracked_variable(
                        domain, alt_rvalue_member_name
                    )

                if rvalue_member_var is None:
                    continue

                # Create equality constraint
                constraint = self._create_equality_constraint(lvalue_member_var, rvalue_member_var)
                if constraint is not None:
                    or_constraints.append(constraint)

            # Apply OR constraint for this struct member
            if or_constraints:
                if len(or_constraints) == 1:
                    # Single constraint, use direct equality
                    self.solver.assert_constraint(or_constraints[0])
                else:
                    # Multiple constraints, use OR
                    or_constraint: SMTTerm = self.solver.Or(*or_constraints)
                    self.solver.assert_constraint(or_constraint)

                self.logger.debug(
                    "Propagated struct member '{lvalue_member}' through Phi from {count} rvalue(s)",
                    lvalue_member=lvalue_member_name,
                    count=len(or_constraints),
                )
