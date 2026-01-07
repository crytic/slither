"""Handler for Member operations (struct member access) in interval analysis."""

from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.declarations.structure import Structure
from slither.slithir.operations.member import Member

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class MemberHandler(BaseOperationHandler):
    """Handle Member operations by tracking struct member accesses and constraining reference variables to equal struct members."""

    def handle(
        self,
        operation: Optional[Member],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        # Guard: ensure we have a valid Member operation
        if operation is None or not isinstance(operation, Member):
            return

        # Guard: solver is required to create SMT variables
        if self.solver is None:
            return

        # Guard: only update when we have a concrete state domain
        if domain.variant != DomainVariant.STATE:
            return

        lvalue = operation.lvalue
        # Guard: nothing to track if there is no lvalue for the member reference
        if lvalue is None:
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        # Guard: skip if we cannot resolve a stable name for the reference
        if lvalue_name is None:
            return

        # Get the struct variable and member name
        struct_var = operation.variable_left
        member_name_const = operation.variable_right

        # Guard: member name must be a constant with a string value
        if not hasattr(member_name_const, "value") or not isinstance(member_name_const.value, str):
            return

        member_name = member_name_const.value

        # Build the struct member variable name (e.g., "user.id" or "user.balance")
        struct_var_name = IntervalSMTUtils.resolve_variable_name(struct_var)
        if struct_var_name is None:
            return

        struct_member_name = f"{struct_var_name}.{member_name}"

        # If the base is a struct and not materialized, materialize its fields.
        struct_type = getattr(struct_var, "type", None)
        if (
            isinstance(struct_type, UserDefinedType)
            and isinstance(struct_type.type, Structure)
            and IntervalSMTUtils.get_tracked_variable(domain, struct_member_name) is None
        ):
            self._materialize_struct_fields(domain, struct_var_name, struct_type.type)

        # Resolve the type for the struct member
        return_type: Optional[ElementaryType] = None

        # Prefer type from lvalue
        if hasattr(lvalue, "type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(lvalue.type)

        # Guard: skip if we cannot determine a supported return type
        if return_type is None:
            return

        if IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            # Guard: unsupported type for interval tracking
            return

        # Get or create tracked variable for the struct member
        struct_member_tracked = IntervalSMTUtils.get_tracked_variable(domain, struct_member_name)
        if struct_member_tracked is None:
            # Create a fresh tracked variable for the struct member
            struct_member_tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver,
                struct_member_name,
                return_type,
            )
            # Guard: creation may fail for unsupported types
            if struct_member_tracked is None:
                return
            domain.state.set_range_variable(struct_member_name, struct_member_tracked)
            struct_member_tracked.assert_no_overflow(self.solver)

        # Get or create tracked variable for the reference (lvalue)
        lvalue_tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if lvalue_tracked is None:
            # Create a fresh tracked variable for the reference
            lvalue_tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver,
                lvalue_name,
                return_type,
            )
            # Guard: creation may fail for unsupported types
            if lvalue_tracked is None:
                return
            domain.state.set_range_variable(lvalue_name, lvalue_tracked)
            lvalue_tracked.assert_no_overflow(self.solver)

        # Constrain the reference to equal the struct member value
        # This models: REF -> struct.member (reading from struct member)
        lvalue_width = self.solver.bv_size(lvalue_tracked.term)
        member_width = self.solver.bv_size(struct_member_tracked.term)

        if lvalue_width != member_width:
            # Handle width mismatch by extending or truncating
            if member_width < lvalue_width:
                is_signed = bool(struct_member_tracked.base.metadata.get("is_signed", False))
                member_term = IntervalSMTUtils.extend_to_width(
                    self.solver, struct_member_tracked.term, lvalue_width, is_signed
                )
            else:
                member_term = IntervalSMTUtils.truncate_to_width(
                    self.solver, struct_member_tracked.term, lvalue_width
                )
            constraint: SMTTerm = lvalue_tracked.term == member_term
        else:
            constraint: SMTTerm = lvalue_tracked.term == struct_member_tracked.term

        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Constrained member reference '{lvalue}' to equal struct member '{member}'",
            lvalue=lvalue_name,
            member=struct_member_name,
        )

    def _materialize_struct_fields(
        self, domain: "IntervalDomain", base_name: str, struct_type: Structure
    ) -> None:
        """Recursively create tracked variables for struct fields down to elementary leaves."""
        if self.solver is None:
            return

        for member in struct_type.elems_ordered:
            member_type = getattr(member, "type", None)
            member_name = getattr(member, "name", None)
            if member_name is None or member_type is None:
                continue

            member_base = f"{base_name}.{member_name}"

            if isinstance(member_type, ElementaryType):
                if IntervalSMTUtils.solidity_type_to_smt_sort(member_type) is None:
                    continue
                tracked = IntervalSMTUtils.get_tracked_variable(domain, member_base)
                if tracked is None:
                    tracked = IntervalSMTUtils.create_tracked_variable(
                        self.solver, member_base, member_type
                    )
                    if tracked is None:
                        continue
                    domain.state.set_range_variable(member_base, tracked)
                continue

            if isinstance(member_type, UserDefinedType) and isinstance(member_type.type, Structure):
                self._materialize_struct_fields(domain, member_base, member_type.type)
                continue

            # Skip unsupported member types (arrays/mappings) for now.
