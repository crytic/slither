"""Handler for Member operations (struct member access) in interval analysis."""

from typing import TYPE_CHECKING, Optional, Tuple

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
    from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
        TrackedSMTVariable,
    )
    from slither.core.cfg.node import Node


class MemberHandler(BaseOperationHandler):
    """Handle Member operations by tracking struct member accesses and constraining refs."""

    def handle(
        self,
        operation: Optional[Member],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        if not self._validate_operation(operation, domain):
            return

        names = self._extract_names(operation, domain)
        if names is None:
            return
        lvalue_name, struct_member_name, return_type = names

        member_var = self._get_or_create_member_var(
            struct_member_name, return_type, domain
        )
        if member_var is None:
            return

        lvalue_var = self._get_or_create_lvalue_var(lvalue_name, return_type, domain)
        if lvalue_var is None:
            return

        self._constrain_lvalue_to_member(
            lvalue_var, member_var, lvalue_name, struct_member_name
        )

    def _validate_operation(
        self, operation: Optional[Member], domain: "IntervalDomain"
    ) -> bool:
        """Validate the operation can be processed."""
        if operation is None or not isinstance(operation, Member):
            return False
        if self.solver is None:
            return False
        if domain.variant != DomainVariant.STATE:
            return False
        if operation.lvalue is None:
            return False
        return True

    def _extract_names(
        self, operation: Member, domain: "IntervalDomain"
    ) -> Optional[Tuple[str, str, ElementaryType]]:
        """Extract lvalue name, struct member name, and return type."""
        lvalue = operation.lvalue
        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return None

        struct_var = operation.variable_left
        member_name_const = operation.variable_right

        # Member name must be a constant with a string value
        if not hasattr(member_name_const, "value"):
            return None
        if not isinstance(member_name_const.value, str):
            return None

        member_name = member_name_const.value

        struct_var_name = IntervalSMTUtils.resolve_variable_name(struct_var)
        if struct_var_name is None:
            return None

        struct_member_name = f"{struct_var_name}.{member_name}"

        # Materialize struct fields if needed
        self._maybe_materialize_struct(struct_var, struct_var_name, struct_member_name, domain)

        # Resolve return type
        return_type: Optional[ElementaryType] = None
        if hasattr(lvalue, "type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(lvalue.type)

        if return_type is None:
            return None
        if IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            return None

        return (lvalue_name, struct_member_name, return_type)

    def _maybe_materialize_struct(
        self,
        struct_var: object,
        struct_var_name: str,
        struct_member_name: str,
        domain: "IntervalDomain",
    ) -> None:
        """Materialize struct fields if base is a struct and not materialized."""
        struct_type = getattr(struct_var, "type", None)
        is_struct = (
            isinstance(struct_type, UserDefinedType)
            and isinstance(struct_type.type, Structure)
        )
        if not is_struct:
            return
        if IntervalSMTUtils.get_tracked_variable(domain, struct_member_name) is not None:
            return
        self._materialize_struct_fields(domain, struct_var_name, struct_type.type)

    def _get_or_create_member_var(
        self,
        struct_member_name: str,
        return_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> Optional["TrackedSMTVariable"]:
        """Get or create tracked variable for struct member."""
        tracked = IntervalSMTUtils.get_tracked_variable(domain, struct_member_name)
        if tracked is not None:
            return tracked

        tracked = IntervalSMTUtils.create_tracked_variable(
            self.solver, struct_member_name, return_type
        )
        if tracked is None:
            return None

        domain.state.set_range_variable(struct_member_name, tracked)
        tracked.assert_no_overflow(self.solver)
        return tracked

    def _get_or_create_lvalue_var(
        self,
        lvalue_name: str,
        return_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> Optional["TrackedSMTVariable"]:
        """Get or create tracked variable for lvalue reference."""
        tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked is not None:
            return tracked

        tracked = IntervalSMTUtils.create_tracked_variable(
            self.solver, lvalue_name, return_type
        )
        if tracked is None:
            return None

        domain.state.set_range_variable(lvalue_name, tracked)
        tracked.assert_no_overflow(self.solver)
        return tracked

    def _constrain_lvalue_to_member(
        self,
        lvalue_var: "TrackedSMTVariable",
        member_var: "TrackedSMTVariable",
        lvalue_name: str,
        member_name: str,
    ) -> None:
        """Constrain the reference to equal the struct member value."""
        lvalue_width = self.solver.bv_size(lvalue_var.term)
        member_width = self.solver.bv_size(member_var.term)

        if lvalue_width != member_width:
            member_term = self._adjust_width(member_var, lvalue_width)
            constraint: SMTTerm = lvalue_var.term == member_term
        else:
            constraint: SMTTerm = lvalue_var.term == member_var.term

        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Constrained member reference '{lvalue}' to equal struct member '{member}'",
            lvalue=lvalue_name,
            member=member_name,
        )

    def _adjust_width(
        self, var: "TrackedSMTVariable", target_width: int
    ) -> SMTTerm:
        """Extend or truncate bitvector to match target width."""
        current_width = self.solver.bv_size(var.term)
        if current_width < target_width:
            is_signed = bool(var.base.metadata.get("is_signed", False))
            return IntervalSMTUtils.extend_to_width(
                self.solver, var.term, target_width, is_signed
            )
        return IntervalSMTUtils.truncate_to_width(self.solver, var.term, target_width)

    def _materialize_struct_fields(
        self, domain: "IntervalDomain", base_name: str, struct_type: Structure
    ) -> None:
        """Recursively create tracked variables for struct fields."""
        if self.solver is None:
            return

        for member in struct_type.elems_ordered:
            self._materialize_single_field(domain, base_name, member)

    def _materialize_single_field(
        self, domain: "IntervalDomain", base_name: str, member: object
    ) -> None:
        """Materialize a single struct field."""
        member_type = getattr(member, "type", None)
        member_name = getattr(member, "name", None)
        if member_name is None or member_type is None:
            return

        member_base = f"{base_name}.{member_name}"

        if isinstance(member_type, ElementaryType):
            self._materialize_elementary_field(domain, member_base, member_type)
            return

        if isinstance(member_type, UserDefinedType) and isinstance(member_type.type, Structure):
            self._materialize_struct_fields(domain, member_base, member_type.type)

    def _materialize_elementary_field(
        self, domain: "IntervalDomain", member_base: str, member_type: ElementaryType
    ) -> None:
        """Materialize an elementary type field."""
        if IntervalSMTUtils.solidity_type_to_smt_sort(member_type) is None:
            return
        if IntervalSMTUtils.get_tracked_variable(domain, member_base) is not None:
            return

        tracked = IntervalSMTUtils.create_tracked_variable(
            self.solver, member_base, member_type
        )
        if tracked is not None:
            domain.state.set_range_variable(member_base, tracked)
