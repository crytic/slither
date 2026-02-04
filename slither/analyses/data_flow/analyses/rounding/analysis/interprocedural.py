"""Goal-directed interprocedural analysis for rounding direction tracking."""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.internal_dynamic_call import InternalDynamicCall
from slither.slithir.operations.phi import Phi

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.analysis import (
        RoundingAnalysis,
    )


@dataclass
class PathConstraint:
    """A constraint along a path to a rounding outcome."""

    expression: str  # The condition expression
    is_true_branch: bool  # Whether we took the true or false branch

    def __str__(self) -> str:
        if self.is_true_branch:
            return self.expression
        return f"!({self.expression})"


@dataclass
class RoundingPath:
    """A path to a specific rounding outcome."""

    tag: RoundingTag
    constraints: list[PathConstraint] = field(default_factory=list)
    call_chain: list[str] = field(default_factory=list)  # Function names
    leaf_operation: str = ""  # e.g., "floor division", "roundDown()"

    def __str__(self) -> str:
        parts = []
        if self.constraints:
            conds = " && ".join(str(c) for c in self.constraints)
            parts.append(f"when: {conds}")
        if self.call_chain:
            parts.append(f"via: {' → '.join(self.call_chain)}")
        parts.append(f"→ {self.leaf_operation}")
        return " | ".join(parts)


@dataclass
class RoundingResult:
    """Result of analyzing a function for rounding behavior."""

    possible_tags: set[RoundingTag] = field(default_factory=set)
    paths: list[RoundingPath] = field(default_factory=list)  # Paths to each tag

    def get_paths_for_tag(self, tag: RoundingTag) -> list[RoundingPath]:
        """Get all paths that lead to a specific tag."""
        return [p for p in self.paths if p.tag == tag]

    def __str__(self) -> str:
        tags = ", ".join(sorted(t.name for t in self.possible_tags))
        return f"{{{tags}}}"


class RoundingInterproceduralAnalyzer:
    """Goal-directed interprocedural analyzer for rounding direction.

    When analyzing with a target tag:
    1. Only explore paths that can lead to the target
    2. Track constraints along the path
    3. Report the path with conditions needed to reach that rounding behavior
    """

    _call_stack: set[Function] = set()

    def __init__(self, analysis: "RoundingAnalysis") -> None:
        self._analysis = analysis
        self._cache: dict[Function, RoundingResult] = {}

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
        target_tag: Optional[RoundingTag] = None,
    ) -> RoundingResult:
        """Analyze a function call for rounding behavior.

        Args:
            callee: The called function
            target_tag: If specified, only find paths to this tag (goal-directed)

        Returns:
            RoundingResult with possible tags and paths
        """
        # Fast path: check if function name indicates rounding
        tag = self._infer_from_name(callee.name)
        if tag != RoundingTag.NEUTRAL:
            # If target specified and doesn't match, return empty
            if target_tag and tag != target_tag:
                return RoundingResult()
            path = RoundingPath(
                tag=tag,
                leaf_operation=f"{callee.name}() [name-based]",
            )
            return RoundingResult(possible_tags={tag}, paths=[path])

        # Check cache (only for full analysis, not goal-directed)
        if target_tag is None and callee in self._cache:
            return self._cache[callee]

        # Recursion detection
        if self.is_in_call_stack(callee):
            return RoundingResult(possible_tags={RoundingTag.UNKNOWN})

        # No implementation
        if not callee.nodes:
            return RoundingResult(possible_tags={RoundingTag.NEUTRAL})

        # Recursive analysis
        self.add_to_call_stack(callee)
        try:
            result = self._analyze_function(callee, target_tag)
            if target_tag is None:
                self._cache[callee] = result
            return result
        finally:
            self.remove_from_call_stack(callee)

    def _handle_division_operation(
        self,
        guard: Optional[PathConstraint],
        target_tag: Optional[RoundingTag],
        result: RoundingResult,
    ) -> None:
        """Handle a division operation during analysis."""
        tag = RoundingTag.DOWN
        if target_tag and tag != target_tag:
            return

        result.possible_tags.add(tag)
        path = RoundingPath(tag=tag, leaf_operation="floor division")
        if guard:
            path.constraints.append(guard)
        result.paths.append(path)

    def _handle_internal_call(
        self,
        callee: Function,
        guard: Optional[PathConstraint],
        target_tag: Optional[RoundingTag],
        result: RoundingResult,
    ) -> None:
        """Handle an internal call operation during analysis."""
        callee_result = self.analyze_call(callee, target_tag)

        for callee_path in callee_result.paths:
            if target_tag and callee_path.tag != target_tag:
                continue

            result.possible_tags.add(callee_path.tag)
            new_path = RoundingPath(
                tag=callee_path.tag,
                constraints=list(callee_path.constraints),
                call_chain=[callee.name] + callee_path.call_chain,
                leaf_operation=callee_path.leaf_operation,
            )
            if guard:
                new_path.constraints.insert(0, guard)
            result.paths.append(new_path)

    def _analyze_function(
        self,
        function: Function,
        target_tag: Optional[RoundingTag] = None,
    ) -> RoundingResult:
        """Analyze a function, optionally goal-directed toward a specific tag."""
        result = RoundingResult()

        for node in function.nodes:
            if not node.irs_ssa:
                continue

            guard = self._get_guard_info(node)

            for operation in node.irs_ssa:
                is_division = (
                    isinstance(operation, Binary)
                    and operation.type == BinaryType.DIVISION
                )
                if is_division:
                    self._handle_division_operation(guard, target_tag, result)

                elif isinstance(operation, InternalCall):
                    callee = operation.function
                    if isinstance(callee, Function):
                        self._handle_internal_call(callee, guard, target_tag, result)

                elif isinstance(operation, InternalDynamicCall):
                    func_variable = operation.function
                    candidates = self._get_dynamic_call_targets(func_variable, function)
                    for callee in candidates:
                        self._handle_internal_call(callee, guard, target_tag, result)

        if not result.possible_tags:
            result.possible_tags.add(RoundingTag.NEUTRAL)

        return result

    def _infer_from_name(self, name: str) -> RoundingTag:
        """Infer rounding direction from function name."""
        name_lower = name.lower()
        if "down" in name_lower or "floor" in name_lower:
            return RoundingTag.DOWN
        elif "up" in name_lower or "ceil" in name_lower:
            return RoundingTag.UP
        return RoundingTag.NEUTRAL

    def _trace_variable_targets(
        self,
        variable: Variable,
        containing_function: Function,
        targets: list[Function],
        visited: set[Variable],
    ) -> None:
        """Recursively trace variable definitions to find function targets."""
        if variable in visited:
            return
        visited.add(variable)

        for node in containing_function.nodes:
            for operation in node.irs_ssa:
                if isinstance(operation, Assignment) and operation.lvalue == variable:
                    if isinstance(operation.rvalue, Function):
                        if operation.rvalue not in targets:
                            targets.append(operation.rvalue)
                    elif isinstance(operation.rvalue, Variable):
                        self._trace_variable_targets(
                            operation.rvalue, containing_function, targets, visited
                        )

                if isinstance(operation, Phi) and operation.lvalue == variable:
                    for rvalue in operation.rvalues:
                        if isinstance(rvalue, Function):
                            if rvalue not in targets:
                                targets.append(rvalue)
                        elif isinstance(rvalue, Variable):
                            self._trace_variable_targets(
                                rvalue, containing_function, targets, visited
                            )

    def _get_dynamic_call_targets(
        self,
        func_variable: Variable,
        containing_function: Function,
    ) -> list[Function]:
        """Find possible function targets for a dynamic call variable.

        In SSA form, when a ternary expression like `cond ? funcA : funcB` is used,
        the function pointer variable is assigned via Assignment operations where
        the rvalue is a Function. We trace all such assignments to find targets.
        """
        targets: list[Function] = []
        visited: set[Variable] = set()
        self._trace_variable_targets(
            func_variable, containing_function, targets, visited
        )
        return targets

    def _get_guard_info(self, node: Node) -> Optional[PathConstraint]:
        """Get the guarding condition for a node."""
        # Find the nearest IF dominator
        for dominator in node.dominators:
            if dominator.type == NodeType.IF and dominator.expression:
                # Determine if we're in true or false branch
                is_true = self._is_in_true_branch(dominator, node)
                return PathConstraint(
                    expression=str(dominator.expression),
                    is_true_branch=is_true,
                )
        return None

    def _is_in_true_branch(self, if_node: Node, target_node: Node) -> bool:
        """Determine if target_node is in the true branch of if_node."""
        # The true branch is typically the first son
        if if_node.sons and len(if_node.sons) >= 1:
            true_branch = if_node.sons[0]
            # Check if target_node is reachable from true_branch
            return self._is_reachable(true_branch, target_node, set())
        return True  # Default to true branch

    def _is_reachable(self, start: Node, target: Node, visited: set[int]) -> bool:
        """Check if target is reachable from start via DFS."""
        if start.node_id == target.node_id:
            return True
        if start.node_id in visited:
            return False
        visited.add(start.node_id)
        for son in start.sons:
            if self._is_reachable(son, target, visited):
                return True
        return False

    def get_trace(
        self,
        function: Function,
        target_tag: RoundingTag,
        indent: int = 0,
    ) -> list[str]:
        """Get a trace showing how a function can produce a given tag."""
        lines: list[str] = []
        prefix = "  " * indent

        # Goal-directed analysis - only find paths to target
        result = self.analyze_call(function, target_tag)
        paths = result.get_paths_for_tag(target_tag)

        for path in paths:
            # Show constraints
            for constraint in path.constraints:
                lines.append(f"{prefix}└─ when {constraint}")
                prefix = prefix + "   "

            # Show call chain (skip last call if it matches the leaf operation)
            call_chain = path.call_chain
            if call_chain and path.leaf_operation.startswith(f"{call_chain[-1]}()"):
                call_chain = call_chain[:-1]

            for call in call_chain:
                lines.append(f"{prefix}→ {call}()")
                prefix = prefix + "  "

            # Show leaf
            lines.append(f"{prefix}→ {path.leaf_operation}")

        return lines

    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self._cache.clear()
