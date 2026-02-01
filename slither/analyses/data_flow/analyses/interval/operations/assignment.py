"""Assignment operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint, Byte
from slither.slithir.operations.assignment import Assignment
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.tuple import TupleVariable
from slither.slithir.utils.utils import LVALUE, RVALUE

from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )

logger = get_logger()


class AssignmentHandler(BaseOperationHandler):
    """Handler for assignment operations."""

    def handle(
        self,
        operation: Assignment,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process assignment operation."""
        lvalue: LVALUE = operation.lvalue
        lvalue_name = lvalue.ssa_name
        lvalue_type = self._get_elementary_type(lvalue, operation)
        if lvalue_type is None:
            return

        sort = self._type_to_sort(lvalue_type)
        tracked_lvalue = TrackedSMTVariable.create(self.solver, lvalue_name, sort)
        self._process_rvalue(operation.rvalue, tracked_lvalue, lvalue_type, domain)
        domain.state.set_variable(lvalue_name, tracked_lvalue)

    def _get_elementary_type(
        self,
        variable: LVALUE,
        operation: Assignment,
    ) -> ElementaryType | None:
        """Extract elementary type from variable or operation."""
        if isinstance(operation.variable_return_type, ElementaryType):
            return operation.variable_return_type
        if isinstance(variable.type, ElementaryType):
            return variable.type
        return None

    def _type_to_sort(self, solidity_type: ElementaryType) -> Sort:
        """Convert Solidity type to SMT sort.

        Raises:
            NotImplementedError: If the type is not supported.
        """
        type_str = solidity_type.type

        if type_str in Uint or type_str in Int:
            width = self._int_bit_width(type_str)
            return Sort(kind=SortKind.BITVEC, parameters=[width])

        if type_str == "bool":
            return Sort(kind=SortKind.BITVEC, parameters=[1])

        if type_str in ("address", "address payable"):
            return Sort(kind=SortKind.BITVEC, parameters=[160])

        if type_str in Byte:
            width = self._byte_bit_width(type_str)
            return Sort(kind=SortKind.BITVEC, parameters=[width])

        supported_types = "uint*, int*, bool, address, address payable, bytes*"
        logger.error_and_raise(
            f"Unsupported type '{type_str}'. Supported: {supported_types}",
            NotImplementedError,
        )

    def _int_bit_width(self, type_str: str) -> int:
        """Get bit width for integer type."""
        if type_str in ("uint", "int"):
            return 256
        if type_str.startswith("uint"):
            return int(type_str[4:])
        if type_str.startswith("int"):
            return int(type_str[3:])
        return 256

    def _byte_bit_width(self, type_str: str) -> int:
        """Get bit width for bytes type."""
        if type_str == "bytes":
            return 256
        if type_str == "byte":
            return 8
        return int(type_str[5:]) * 8

    def _process_rvalue(
        self,
        rvalue: Union[RVALUE, Function, TupleVariable],
        tracked_lvalue: TrackedSMTVariable,
        lvalue_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> None:
        """Process rvalue and assert equality constraint."""
        if isinstance(rvalue, Constant):
            self._handle_constant(rvalue, tracked_lvalue)
            return

        # For non-constant rvalues that have ssa_name
        rvalue_name = rvalue.ssa_name
        self._handle_variable(rvalue_name, rvalue, tracked_lvalue, lvalue_type, domain)

    def _handle_constant(
        self,
        constant: Constant,
        tracked_lvalue: TrackedSMTVariable,
    ) -> None:
        """Handle constant rvalue."""
        value = constant.value
        if not isinstance(value, (int, bool)):
            return

        int_value = 1 if value is True else (0 if value is False else value)
        width = self.solver.bv_size(tracked_lvalue.term)
        const_term = self.solver.create_constant(
            int_value,
            Sort(kind=SortKind.BITVEC, parameters=[width]),
        )
        self.solver.assert_constraint(tracked_lvalue.term == const_term)

    def _handle_variable(
        self,
        rvalue_name: str,
        rvalue: RVALUE,
        tracked_lvalue: TrackedSMTVariable,
        lvalue_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> None:
        """Handle variable rvalue."""
        tracked_rvalue = domain.state.get_variable(rvalue_name)

        if tracked_rvalue is None:
            rvalue_type = rvalue.type if isinstance(rvalue.type, ElementaryType) else lvalue_type
            sort = self._type_to_sort(rvalue_type)
            tracked_rvalue = TrackedSMTVariable.create(self.solver, rvalue_name, sort)
            domain.state.set_variable(rvalue_name, tracked_rvalue)

        self.solver.assert_constraint(tracked_lvalue.term == tracked_rvalue.term)
