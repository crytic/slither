"""Handler for NewStructure operations (struct construction)."""

from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.core.declarations.structure import Structure
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.slithir.operations.new_structure import NewStructure
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
        TrackedSMTVariable,
    )
    from slither.core.cfg.node import Node


class NewStructureHandler(BaseOperationHandler):
    """Materialize struct fields when a NewStructure IR operation is encountered."""

    def handle(
        self,
        operation: Optional[NewStructure],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        if operation is None or not isinstance(operation, NewStructure):
            return
        if self.solver is None:
            return
        if domain.variant != DomainVariant.STATE:
            return

        struct: Structure = operation.structure
        lvalue_name = IntervalSMTUtils.resolve_variable_name(operation.lvalue)
        if lvalue_name is None:
            return

        self._materialize_struct(domain, lvalue_name, struct, operation.arguments)

    def _materialize_struct(
        self,
        domain: "IntervalDomain",
        base_name: str,
        struct: Structure,
        args: list,
    ) -> None:
        """Recursively create tracked variables for struct fields and bind constructor args."""
        for idx, member in enumerate(struct.elems_ordered):
            member_type = getattr(member, "type", None)
            member_name = getattr(member, "name", None)
            if member_name is None or member_type is None:
                continue

            field_name = f"{base_name}.{member_name}"

            # Elementary field
            if isinstance(member_type, ElementaryType):
                if IntervalSMTUtils.solidity_type_to_smt_sort(member_type) is None:
                    continue
                tracked = IntervalSMTUtils.get_tracked_variable(domain, field_name)
                if tracked is None:
                    tracked = IntervalSMTUtils.create_tracked_variable(
                        self.solver, field_name, member_type
                    )
                    if tracked is None:
                        continue
                    domain.state.set_range_variable(field_name, tracked)

                # Bind constructor argument when available
                if idx < len(args):
                    arg_term = self._resolve_arg_term(args[idx], tracked, member_type, domain)
                    if arg_term is not None:
                        self.solver.assert_constraint(tracked.term == arg_term)
                        tracked.assert_no_overflow(self.solver)
                continue

            # Nested struct
            if isinstance(member_type, UserDefinedType) and isinstance(member_type.type, Structure):
                self._materialize_struct(domain, field_name, member_type.type, args=[])
                continue

            # Skip unsupported types (arrays/mappings) for now.

    def _resolve_arg_term(
        self,
        arg: object,
        target: "TrackedSMTVariable",
        target_type: ElementaryType,
        domain: "IntervalDomain",
    ):
        """Resolve constructor argument to an SMT term aligned with target width."""
        if self.solver is None:
            return None

        if isinstance(arg, Constant) and isinstance(arg.value, int):
            return IntervalSMTUtils.create_constant_term(self.solver, arg.value, target_type)

        arg_name = IntervalSMTUtils.resolve_variable_name(arg)
        if arg_name is None:
            return None

        arg_tracked = IntervalSMTUtils.get_tracked_variable(domain, arg_name)
        if arg_tracked is None:
            return None

        arg_term = arg_tracked.term
        target_width = self.solver.bv_size(target.term)
        arg_width = self.solver.bv_size(arg_term)
        if arg_width < target_width:
            is_signed = bool(arg_tracked.base.metadata.get("is_signed", False))
            return IntervalSMTUtils.extend_to_width(self.solver, arg_term, target_width, is_signed)
        if arg_width > target_width:
            return IntervalSMTUtils.truncate_to_width(self.solver, arg_term, target_width)
        return arg_term

