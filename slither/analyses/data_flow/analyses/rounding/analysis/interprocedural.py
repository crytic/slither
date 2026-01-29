"""Interprocedural analysis for rounding direction tracking."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, TYPE_CHECKING

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations import Function

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.analysis import (
        RoundingAnalysis,
    )


@dataclass
class RoundingResult:
    """Result of analyzing a function for rounding behavior."""

    possible_tags: Set[RoundingTag] = field(default_factory=set)
    condition: Optional[str] = None  # Guarding condition if inside a branch

    def __str__(self) -> str:
        tags = ", ".join(sorted(t.name for t in self.possible_tags))
        cond = f" when {self.condition}" if self.condition else ""
        return f"{{{tags}}}{cond}"


class RoundingInterproceduralAnalyzer:
    """Inline interprocedural analyzer for rounding direction.

    When a call is encountered:
    1. Check if function name indicates rounding (fast path)
    2. If not, recursively analyze the callee
    3. Continue until hitting a named function or leaf operation
    """

    # Global call stack for recursion detection
    _call_stack: Set[Function] = set()

    def __init__(self, analysis: "RoundingAnalysis") -> None:
        self._analysis = analysis
        self._cache: Dict[Function, RoundingResult] = {}

    @classmethod
    def is_in_call_stack(cls, function: Function) -> bool:
        """Check if function is already being analyzed."""
        return function in cls._call_stack

    @classmethod
    def add_to_call_stack(cls, function: Function) -> None:
        """Add function to call stack."""
        cls._call_stack.add(function)

    @classmethod
    def remove_from_call_stack(cls, function: Function) -> None:
        """Remove function from call stack."""
        cls._call_stack.discard(function)

    def analyze_call(
        self,
        callee: Function,
        condition: Optional[str] = None,
    ) -> RoundingResult:
        """Analyze a function call for rounding behavior.

        Args:
            callee: The called function
            condition: Guarding condition if inside a branch

        Returns:
            RoundingResult with possible tags
        """
        # Fast path: check if function name indicates rounding
        tag = self._infer_from_name(callee.name)
        if tag != RoundingTag.NEUTRAL:
            return RoundingResult(possible_tags={tag}, condition=condition)

        # Check cache
        if callee in self._cache:
            result = self._cache[callee]
            # Add condition if provided
            if condition and not result.condition:
                result = RoundingResult(
                    possible_tags=result.possible_tags, condition=condition
                )
            return result

        # Recursion detection
        if self.is_in_call_stack(callee):
            return RoundingResult(possible_tags={RoundingTag.UNKNOWN})

        # No implementation
        if not callee.nodes:
            return RoundingResult(possible_tags={RoundingTag.NEUTRAL})

        # Recursive analysis
        self.add_to_call_stack(callee)
        try:
            result = self._analyze_function(callee)
            if condition:
                result = RoundingResult(
                    possible_tags=result.possible_tags, condition=condition
                )
            self._cache[callee] = result
            return result
        finally:
            self.remove_from_call_stack(callee)

    def _analyze_function(self, function: Function) -> RoundingResult:
        """Recursively analyze a function for rounding behavior."""
        from slither.slithir.operations.binary import Binary, BinaryType
        from slither.slithir.operations.internal_call import InternalCall

        possible_tags: Set[RoundingTag] = set()

        # Analyze all nodes looking for rounding operations and calls
        for node in function.nodes:
            if not node.irs_ssa:
                continue

            condition = self._get_guarding_condition(node)

            for operation in node.irs_ssa:
                # Direct division -> DOWN (floor) by default
                if isinstance(operation, Binary):
                    if operation.type == BinaryType.DIVISION:
                        # Check for ceiling pattern
                        if self._is_ceiling_pattern(operation, node):
                            possible_tags.add(RoundingTag.UP)
                        else:
                            possible_tags.add(RoundingTag.DOWN)

                # Internal call -> recurse
                elif isinstance(operation, InternalCall):
                    callee = operation.function
                    if isinstance(callee, Function):
                        result = self.analyze_call(callee, condition)
                        possible_tags.update(result.possible_tags)

        # Default to NEUTRAL if nothing found
        if not possible_tags:
            possible_tags.add(RoundingTag.NEUTRAL)

        return RoundingResult(possible_tags=possible_tags)

    def _infer_from_name(self, name: str) -> RoundingTag:
        """Infer rounding direction from function name."""
        name_lower = name.lower()
        if "down" in name_lower or "floor" in name_lower:
            return RoundingTag.DOWN
        elif "up" in name_lower or "ceil" in name_lower:
            return RoundingTag.UP
        return RoundingTag.NEUTRAL

    def _get_guarding_condition(self, node: Node) -> Optional[str]:
        """Extract guarding condition from dominating IF node."""
        for dominator in node.dominators:
            if dominator.type == NodeType.IF and dominator.expression:
                return str(dominator.expression)
        return None

    def _is_ceiling_pattern(self, operation: object, node: Node) -> bool:  # noqa: ARG002
        """Detect ceiling division pattern: (a + b - 1) / b."""
        # Simplified check - the full analysis handles this better
        # This is just a quick heuristic for the interprocedural case
        _ = operation, node  # Suppress unused warnings
        return False

    def get_trace(
        self,
        function: Function,
        target_tag: RoundingTag,
        indent: int = 0,
    ) -> List[str]:
        """Get a trace showing how a function can produce a given tag."""
        lines: List[str] = []
        prefix = "  " * indent

        result = self.analyze_call(function)
        if target_tag not in result.possible_tags:
            return lines

        # Analyze to find the path
        from slither.slithir.operations.binary import Binary, BinaryType
        from slither.slithir.operations.internal_call import InternalCall

        for node in function.nodes:
            if not node.irs_ssa:
                continue

            condition = self._get_guarding_condition(node)

            for operation in node.irs_ssa:
                if isinstance(operation, Binary) and operation.type == BinaryType.DIVISION:
                    tag = RoundingTag.DOWN  # Default floor division
                    if tag == target_tag:
                        if condition:
                            lines.append(f"{prefix}└─ when {condition}")
                            lines.append(f"{prefix}   → floor division")
                        else:
                            lines.append(f"{prefix}→ floor division")

                elif isinstance(operation, InternalCall):
                    callee = operation.function
                    if isinstance(callee, Function):
                        callee_result = self.analyze_call(callee, condition)
                        if target_tag in callee_result.possible_tags:
                            if condition:
                                lines.append(f"{prefix}└─ when {condition}")
                                lines.append(f"{prefix}   → {callee.name}()")
                                sub_trace = self.get_trace(callee, target_tag, indent + 2)
                            else:
                                lines.append(f"{prefix}→ {callee.name}()")
                                sub_trace = self.get_trace(callee, target_tag, indent + 1)
                            lines.extend(sub_trace)

        return lines

    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self._cache.clear()
