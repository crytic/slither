"""Handler for Length operations (array/bytes length access) in interval analysis."""

from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.length import Length
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class LengthHandler(BaseOperationHandler):
    """Handle Length operations by returning actual length for constants, or full uint256 range for dynamic values."""

    def handle(
        self,
        operation: Optional[Length],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        # Guard: ensure we have a valid Length operation
        if operation is None or not isinstance(operation, Length):
            return

        # Guard: solver is required to create SMT variables
        if self.solver is None:
            return

        # Guard: only update when we have a concrete state domain
        if domain.variant != DomainVariant.STATE:
            return

        lvalue = operation.lvalue
        # Guard: nothing to track if there is no lvalue for the length result
        if lvalue is None:
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        # Guard: skip if we cannot resolve a stable name for the result
        if lvalue_name is None:
            return

        # Length always returns uint256
        result_type = ElementaryType("uint256")

        # Get or create tracked variable for the lvalue (length result)
        lvalue_tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if lvalue_tracked is None:
            # Create a fresh tracked variable for the length result
            lvalue_tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver,
                lvalue_name,
                result_type,
            )
            # Guard: creation may fail for unsupported types
            if lvalue_tracked is None:
                return
            domain.state.set_range_variable(lvalue_name, lvalue_tracked)
            lvalue_tracked.assert_no_overflow(self.solver)

        # Get the value we're taking the length of
        value = operation.value

        # Check if the value is a constant (hardcoded bytes/string)
        if isinstance(value, Constant):
            const_value = value.value
            # Handle bytes/string constants - get their actual length
            if isinstance(const_value, (bytes, str)):
                actual_length = len(const_value)
                const_term: SMTTerm = self.solver.create_constant(
                    actual_length, lvalue_tracked.sort
                )
                constraint: SMTTerm = lvalue_tracked.term == const_term
                self.solver.assert_constraint(constraint)
                self.logger.debug(
                    "Constrained length of constant to {length}",
                    length=actual_length,
                )
                return
            # Handle list/array constants
            if isinstance(const_value, (list, tuple)):
                actual_length = len(const_value)
                const_term: SMTTerm = self.solver.create_constant(
                    actual_length, lvalue_tracked.sort
                )
                constraint: SMTTerm = lvalue_tracked.term == const_term
                self.solver.assert_constraint(constraint)
                self.logger.debug(
                    "Constrained length of constant array to {length}",
                    length=actual_length,
                )
                return

        # Check if the value is a variable with known byte length from assignment
        value_name = IntervalSMTUtils.resolve_variable_name(value)
        if value_name is not None:
            value_tracked = IntervalSMTUtils.get_tracked_variable(domain, value_name)

            # If not found, try prefix-based lookup for SSA-versioned variables
            # Domain stores "Foo.bar|bar_1" but value_name may be "Foo.bar"
            if value_tracked is None:
                candidate_vars = domain.state.get_variables_by_prefix(value_name + "|")
                for var_name in candidate_vars:
                    value_tracked = domain.state.range_variables.get(var_name)
                    if value_tracked is not None:
                        break

            if value_tracked is not None:
                # Check for byte length metadata stored during constant assignment
                bytes_length = value_tracked.base.metadata.get("bytes_length")
                if bytes_length is not None:
                    const_term: SMTTerm = self.solver.create_constant(
                        bytes_length, lvalue_tracked.sort
                    )
                    constraint: SMTTerm = lvalue_tracked.term == const_term
                    self.solver.assert_constraint(constraint)
                    self.logger.debug(
                        "Constrained length from metadata: {value} has length {length}",
                        value=value_name,
                        length=bytes_length,
                    )
                    return

        # For dynamic values, the length is unconstrained (full uint256 range)
        # but we still need to ensure it's non-negative (already guaranteed by uint256)
        self.logger.debug(
            "Handled length operation: LENGTH {value} -> {lvalue} (dynamic range)",
            value=value,
            lvalue=lvalue_name,
        )
