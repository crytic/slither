"""Base handler for interprocedural analysis of function calls."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.analyses.data_flow.analyses.rounding.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    get_variable_tag,
    infer_tag_from_name,
)
from slither.core.cfg.node import Node
from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.call import Call

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )


class InterproceduralHandler(BaseOperationHandler):
    """Base handler for function calls requiring interprocedural analysis.

    Subclasses should implement:
    - _get_called_function: Extract the Function object from the operation
    - _get_function_name: Get the function name for name-based inference
    """

    def handle(
        self,
        operation: Call,
        domain: "RoundingDomain",
        node: Node,
    ) -> None:
        """Process call operation with interprocedural analysis."""
        if not operation.lvalue:
            return

        function_name = self._get_function_name(operation)

        if self._is_named_division_function(function_name):
            self._check_named_division_consistency(operation, domain, node)

        tag = infer_tag_from_name(function_name)
        if tag != RoundingTag.NEUTRAL:
            self._set_tag(operation.lvalue, tag, operation, node, domain)
            return

        tag = self._analyze_interprocedurally(operation)
        self._set_tag(operation.lvalue, tag, operation, node, domain)

    @abstractmethod
    def _get_called_function(self, operation: Call) -> Function | None:
        """Extract the called Function from the operation."""

    @abstractmethod
    def _get_function_name(self, operation: Call) -> str:
        """Get the function name for name-based inference."""

    def _analyze_interprocedurally(self, operation: Call) -> RoundingTag:
        """Perform interprocedural analysis on the called function."""
        if not self.analysis._interprocedural:
            return RoundingTag.NEUTRAL

        callee = self._get_called_function(operation)
        if callee is None or not callee.nodes:
            return RoundingTag.NEUTRAL

        result = self.analysis._interprocedural.analyze_call(callee)
        return self._derive_tag_from_result(result.possible_tags)

    def _derive_tag_from_result(self, tags: set) -> RoundingTag:
        """Derive a single tag from interprocedural result.

        Rules:
        - Single tag -> use it
        - Multiple non-NEUTRAL tags -> UNKNOWN (conservative)
        - Multiple with only one non-NEUTRAL -> use that tag
        """
        if not tags:
            return RoundingTag.NEUTRAL

        if len(tags) == 1:
            return next(iter(tags))

        non_neutral = {t for t in tags if t != RoundingTag.NEUTRAL}

        if not non_neutral:
            return RoundingTag.NEUTRAL

        if len(non_neutral) == 1:
            return next(iter(non_neutral))

        return RoundingTag.UNKNOWN

    def _is_named_division_function(self, function_name: str) -> bool:
        """Return True when function name indicates divUp/divDown helpers."""
        name_lower = function_name.lower()
        return "divup" in name_lower or "divdown" in name_lower

    def _check_named_division_consistency(
        self,
        operation: Call,
        domain: "RoundingDomain",
        node: Node,
    ) -> None:
        """Enforce division consistency for divUp/divDown call arguments."""
        if len(operation.arguments) < 2:
            return

        numerator = operation.arguments[0]
        denominator = operation.arguments[1]
        numerator_tag = get_variable_tag(numerator, domain)
        denominator_tag = get_variable_tag(denominator, domain)
        inconsistency_reason = self._check_division_consistency(
            numerator_tag, denominator_tag, operation, node
        )
        if inconsistency_reason and operation.lvalue:
            domain.state.set_tag(
                operation.lvalue,
                RoundingTag.UNKNOWN,
                operation,
                unknown_reason=inconsistency_reason,
            )

    def _check_division_consistency(
        self,
        numerator_tag: RoundingTag,
        denominator_tag: RoundingTag,
        operation: Call,
        node: Node,
    ) -> Optional[str]:
        """Check numerator/denominator consistency for division operations."""
        if denominator_tag == RoundingTag.NEUTRAL:
            return None

        if numerator_tag == denominator_tag:
            function_name = node.function.name
            reason = (
                "Inconsistent division: numerator and denominator both "
                f"{numerator_tag.name} in {function_name}"
            )
            message = (
                "Division rounding inconsistency in "
                f"{function_name}: numerator and denominator both "
                f"{numerator_tag.name} in {operation}"
            )
            self.analysis.inconsistencies.append(message)
            self.analysis._logger.error(message)
            return reason
        return None

    def _set_tag(
        self,
        variable: object,
        tag: RoundingTag,
        operation: Call,
        node: Node,
        domain: "RoundingDomain",
    ) -> None:
        """Set tag and check annotation."""
        if not isinstance(variable, Variable):
            return
        domain.state.set_tag(variable, tag, operation)
        self.analysis._check_annotation_for_variable(
            variable, tag, operation, node, domain
        )
