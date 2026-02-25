"""Type conversion operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.type_conversion import TypeConversion
from slither.slithir.variables.constant import Constant

from slither.analyses.data_flow.smt_solver.types import SMTTerm, Sort, SortKind
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_variable_name,
    is_signed_type,
    get_bit_width,
    constant_to_term,
    try_create_parameter_variable,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.width_matching import (
    match_width,
    match_width_to_int,
)

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )

# Re-export for backward compatibility — many modules import from here
__all__ = [
    "match_width",
    "match_width_to_int",
    "TypeConversionHandler",
]


class TypeConversionHandler(BaseOperationHandler):
    """Handler for type conversion operations.

    Supports widening, narrowing, and sign conversions between integer types.
    """

    def handle(
        self,
        operation: TypeConversion,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process type conversion operation."""
        target_type = operation.type
        if not isinstance(target_type, ElementaryType):
            return

        result_name = get_variable_name(operation.lvalue)
        target_width = get_bit_width(target_type)
        target_signed = is_signed_type(target_type)

        result_var = self._create_result_variable(result_name, target_width, target_signed)
        source_term = self._resolve_source(operation, domain)

        if source_term is not None:
            converted_term = self._convert_term(source_term, operation, target_width)
            self.solver.assert_constraint(result_var.term == converted_term)

        domain.state.set_variable(result_name, result_var)

    def _create_result_variable(
        self,
        name: str,
        bit_width: int,
        is_signed: bool,
    ) -> TrackedSMTVariable:
        """Create a tracked variable for the conversion result."""
        sort = Sort(kind=SortKind.BITVEC, parameters=[bit_width])
        return TrackedSMTVariable.create(
            self.solver, name, sort, is_signed=is_signed, bit_width=bit_width
        )

    def _resolve_source(
        self,
        operation: TypeConversion,
        domain: "IntervalDomain",
    ) -> SMTTerm | None:
        """Resolve the source variable to an SMT term."""
        source = operation.variable

        if isinstance(source, Constant):
            return self._resolve_constant(source)

        source_name = get_variable_name(source)
        tracked = domain.state.get_variable(source_name)

        if tracked is not None:
            return tracked.term

        tracked = try_create_parameter_variable(
            self.solver, source, source_name, domain
        )
        if tracked is not None:
            return tracked.term

        return None

    def _resolve_constant(self, constant: Constant) -> SMTTerm | None:
        """Resolve a constant source to an SMT term."""
        value = constant.value
        if not isinstance(value, (int, bool)):
            return None
        source_type = constant.type
        if not isinstance(source_type, ElementaryType):
            return None
        width = get_bit_width(source_type)
        return constant_to_term(self.solver, value, width)

    def _convert_term(
        self,
        source_term: SMTTerm,
        operation: TypeConversion,
        target_width: int,
    ) -> SMTTerm:
        """Convert source term to target width with appropriate extension."""
        source_width = self.solver.bv_size(source_term)

        if source_width == target_width:
            return source_term

        if source_width > target_width:
            return self.solver.bv_extract(source_term, target_width - 1, 0)

        source_type = operation.variable.type
        source_signed = isinstance(source_type, ElementaryType) and is_signed_type(source_type)
        extra_bits = target_width - source_width

        if source_signed:
            return self.solver.bv_sign_ext(source_term, extra_bits)
        return self.solver.bv_zero_ext(source_term, extra_bits)
