"""Base class for operation handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from slither.slithir.operations import Operation
from slither.slithir.variables.constant import Constant
from slither.core.cfg.node import Node

from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.analyses.data_flow.analyses.interval.operations.width_matching import (
    match_width_to_int,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    constant_to_term,
    get_variable_name,
    try_create_parameter_variable,
    try_create_solidity_variable,
    try_create_state_variable,
    try_create_top_level_variable,
)

if TYPE_CHECKING:
    from slither.slithir.utils.utils import RVALUE
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )


class BaseOperationHandler(ABC):
    """Abstract base class for operation handlers."""

    def __init__(self, solver: "SMTSolver"):
        self._solver = solver

    @property
    def solver(self) -> "SMTSolver":
        return self._solver

    @abstractmethod
    def handle(
        self,
        operation: Operation,
        domain: "IntervalDomain",
        node: Node,
    ) -> None:
        """Process operation, modifying domain in-place."""

    def _resolve_operand(
        self,
        operand: "RVALUE",
        domain: "IntervalDomain",
        target_width: int,
    ) -> SMTTerm | None:
        """Resolve an operand to an SMT term with width matching.

        Looks up the operand in the domain state, creating tracked
        variables for parameters and Solidity built-ins as needed.
        The returned term is width-matched to target_width.

        Args:
            operand: The operand to resolve.
            domain: The interval domain containing tracked variables.
            target_width: The bit width to match the result to.

        Returns:
            Width-matched SMT term, or None if the operand cannot
            be resolved.
        """
        if isinstance(operand, Constant):
            return self._constant_to_term(operand, target_width)

        operand_name = get_variable_name(operand)
        tracked = domain.state.get_variable(operand_name)

        if tracked is not None:
            return match_width_to_int(
                self.solver, tracked.term, target_width
            )

        tracked = try_create_parameter_variable(
            self.solver, operand, operand_name, domain
        )
        if tracked is not None:
            return match_width_to_int(
                self.solver, tracked.term, target_width
            )

        tracked = try_create_solidity_variable(
            self.solver, operand, operand_name, domain
        )
        if tracked is not None:
            return match_width_to_int(
                self.solver, tracked.term, target_width
            )

        tracked = try_create_state_variable(
            self.solver, operand, operand_name, domain
        )
        if tracked is not None:
            return match_width_to_int(
                self.solver, tracked.term, target_width
            )

        tracked = try_create_top_level_variable(
            self.solver, operand, operand_name, domain
        )
        if tracked is not None:
            return match_width_to_int(
                self.solver, tracked.term, target_width
            )

        return None

    def _constant_to_term(
        self,
        constant: Constant,
        bit_width: int,
    ) -> SMTTerm | None:
        """Convert a constant to an SMT term.

        Args:
            constant: The constant to convert.
            bit_width: The bit width for the resulting term.

        Returns:
            SMT term for the constant, or None if unsupported.
        """
        value = constant.value
        if isinstance(value, bool):
            return constant_to_term(
                self.solver, 1 if value else 0, bit_width
            )
        if isinstance(value, int):
            return constant_to_term(self.solver, value, bit_width)
        return None
