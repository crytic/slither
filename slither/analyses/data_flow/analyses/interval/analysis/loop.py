"""Static loop metadata used by interval widening."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.engine.loop import (
    LoopStructure,
    LoopVariableId,
    LoopWideningContext,
)
from slither.analyses.data_flow.smt_solver.facts import LoopHeaderId
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.condition import Condition
from slither.slithir.operations.phi import Phi
from slither.slithir.variables.constant import Constant


if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.core.state import State
    from slither.core.cfg.node import Node
    from slither.core.declarations.function import Function
    from slither.slithir.operations.operation import Operation


PRECISE_LOOP_GENERATION_LIMIT = 64


def _variable_name(value: object) -> str:
    """Return an SSA or ordinary name for metadata-only inspection."""
    ssa_name = getattr(value, "ssa_name", None)
    if isinstance(ssa_name, str):
        return ssa_name
    name = getattr(value, "name", None)
    if not isinstance(name, str):
        raise TypeError(f"Loop operand {value!r} has no variable name")
    return name


@dataclass(frozen=True)
class LoopProgression:
    """Certified monotone induction variable controlling one loop exit."""

    variable: LoopVariableId
    comparison: BinaryType
    bound: int
    step: int

    def maximum_iterations(self, state: State) -> int | None:
        """Return a conservative finite trip bound from the entry interval."""
        entry_interval = None
        for name in self.variable.entry_names:
            tracked = state.get_variable(name)
            if tracked is None:
                return None
            entry_interval = (
                tracked.interval
                if entry_interval is None
                else entry_interval.hull(tracked.interval)
            )
        if entry_interval is None:
            return None
        if self.step > 0:
            target = self.bound + int(self.comparison is BinaryType.LESS_EQUAL)
            distance = max(0, target - entry_interval.lower)
            return (distance + self.step - 1) // self.step
        target = self.bound - int(self.comparison is BinaryType.GREATER_EQUAL)
        distance = max(0, entry_interval.upper - target)
        magnitude = -self.step
        return (distance + magnitude - 1) // magnitude

    def exhaustively_unrolled(self, context: LoopWideningContext) -> bool:
        """Return whether a bounded loop has reached its certified trip limit."""
        current = context.current_input
        previous_output = context.previous_output
        if not isinstance(current, IntervalDomain) or not isinstance(
            previous_output, IntervalDomain
        ):
            return False
        if current.variant is not DomainVariant.STATE or current.state is None:
            return False
        if previous_output.variant is not DomainVariant.STATE or previous_output.state is None:
            return False
        maximum = self.maximum_iterations(current.state)
        if maximum is None or maximum > PRECISE_LOOP_GENERATION_LIMIT:
            return False
        if context.generation <= maximum:
            return False
        header_value = previous_output.state.get_variable(self.variable.header_name)
        if header_value is None:
            return False
        if self.step > 0:
            return header_value.interval.upper >= self.bound
        return header_value.interval.lower <= self.bound


class IntervalLoopMetadata:
    """Loop-carried SSA bindings and certified finite progressions."""

    def __init__(
        self,
        variables: dict[LoopHeaderId, tuple[LoopVariableId, ...]] | None = None,
        progressions: dict[LoopHeaderId, LoopProgression] | None = None,
    ) -> None:
        self._variables = dict(variables or {})
        self._progressions = dict(progressions or {})

    @classmethod
    def from_function(cls, function: Function) -> IntervalLoopMetadata:
        """Derive metadata solely from stable SSA and dominator information."""
        structure = LoopStructure.from_function(function)
        nodes = {node.node_id: node for node in function.nodes}
        definitions = cls._definitions(function)
        variables = {}
        progressions = {}
        for loop in structure.loops:
            header = nodes[loop.header_id.node_id]
            bindings = cls._loop_variables(header, definitions)
            variables[loop.header_id] = bindings
            progression = cls._progression(header, bindings, definitions)
            if progression is not None:
                progressions[loop.header_id] = progression
        return cls(variables, progressions)

    @staticmethod
    def _definitions(function: Function) -> dict[str, tuple[Operation, Node]]:
        definitions = {}
        for node in function.nodes:
            for operation in node.irs_ssa or ():
                lvalue = getattr(operation, "lvalue", None)
                if lvalue is not None:
                    definitions[_variable_name(lvalue)] = (operation, node)
        return definitions

    @staticmethod
    def _loop_variables(
        header: Node,
        definitions: dict[str, tuple[Operation, Node]],
    ) -> tuple[LoopVariableId, ...]:
        variables = []
        for operation in header.irs_ssa or ():
            if not isinstance(operation, Phi) or operation.lvalue is None:
                continue
            entry_names = []
            back_names = []
            for rvalue in operation.rvalues:
                name = _variable_name(rvalue)
                definition = definitions.get(name)
                is_back = definition is not None and header in definition[1].dominators
                (back_names if is_back else entry_names).append(name)
            if entry_names and back_names:
                variables.append(
                    LoopVariableId(
                        _variable_name(operation.lvalue),
                        tuple(sorted(entry_names)),
                        tuple(sorted(back_names)),
                    )
                )
        return tuple(sorted(variables))

    @classmethod
    def _progression(
        cls,
        header: Node,
        variables: tuple[LoopVariableId, ...],
        definitions: dict[str, tuple[Operation, Node]],
    ) -> LoopProgression | None:
        comparison = cls._condition_comparison(header)
        if comparison is None:
            return None
        for variable in variables:
            normalized = cls._normalize_comparison(comparison, variable.header_name)
            if normalized is None:
                continue
            comparison_type, bound = normalized
            steps = {
                cls._progression_step(definitions.get(name), variable.header_name)
                for name in variable.back_names
            }
            if None in steps or len(steps) != 1:
                continue
            step = steps.pop()
            if step is None or not cls._moves_toward_exit(comparison_type, step):
                continue
            return LoopProgression(variable, comparison_type, bound, step)
        return None

    @staticmethod
    def _condition_comparison(header: Node) -> Binary | None:
        operations = header.irs_ssa or ()
        conditions = [operation for operation in operations if isinstance(operation, Condition)]
        if len(conditions) != 1:
            return None
        condition_name = _variable_name(conditions[0].value)
        return next(
            (
                operation
                for operation in operations
                if isinstance(operation, Binary)
                and operation.lvalue is not None
                and _variable_name(operation.lvalue) == condition_name
            ),
            None,
        )

    @staticmethod
    def _normalize_comparison(
        operation: Binary,
        variable_name: str,
    ) -> tuple[BinaryType, int] | None:
        left_name = _variable_name(operation.variable_left)
        right_name = _variable_name(operation.variable_right)
        if left_name == variable_name and isinstance(operation.variable_right, Constant):
            value = operation.variable_right.value
            return (operation.type, value) if isinstance(value, int) else None
        if right_name != variable_name or not isinstance(operation.variable_left, Constant):
            return None
        value = operation.variable_left.value
        if not isinstance(value, int):
            return None
        reversed_types = {
            BinaryType.LESS: BinaryType.GREATER,
            BinaryType.LESS_EQUAL: BinaryType.GREATER_EQUAL,
            BinaryType.GREATER: BinaryType.LESS,
            BinaryType.GREATER_EQUAL: BinaryType.LESS_EQUAL,
        }
        reversed_type = reversed_types.get(operation.type)
        return (reversed_type, value) if reversed_type is not None else None

    @staticmethod
    def _progression_step(
        definition: tuple[Operation, Node] | None,
        header_name: str,
    ) -> int | None:
        if definition is None:
            return None
        raw_operation, node = definition
        if not isinstance(raw_operation, Binary):
            return None
        operation = raw_operation
        if not bool(getattr(node.scope, "is_checked", False)):
            return None
        left = operation.variable_left
        right = operation.variable_right
        if operation.type is BinaryType.ADDITION:
            if _variable_name(left) == header_name and isinstance(right, Constant):
                return right.value if isinstance(right.value, int) else None
            if _variable_name(right) == header_name and isinstance(left, Constant):
                return left.value if isinstance(left.value, int) else None
        if (
            operation.type is BinaryType.SUBTRACTION
            and _variable_name(left) == header_name
            and isinstance(right, Constant)
            and isinstance(right.value, int)
        ):
            return -right.value
        return None

    @staticmethod
    def _moves_toward_exit(comparison: BinaryType, step: int) -> bool:
        ascending = comparison in (BinaryType.LESS, BinaryType.LESS_EQUAL)
        descending = comparison in (BinaryType.GREATER, BinaryType.GREATER_EQUAL)
        return (ascending and step > 0) or (descending and step < 0)

    def variables_for(self, header_id: LoopHeaderId) -> tuple[LoopVariableId, ...]:
        """Return loop-carried bindings for one header."""
        return self._variables.get(header_id, ())

    def is_loop_header(self, header_id: LoopHeaderId) -> bool:
        """Return whether the stable header belongs to a classified natural loop."""
        return header_id in self._variables

    def progression_for(self, header_id: LoopHeaderId) -> LoopProgression | None:
        """Return the certified controlling progression, when available."""
        return self._progressions.get(header_id)
