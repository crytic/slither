"""Natural-loop identities and generation-scoped header fixpoints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.smt_solver.facts import Fact, FactId, LoopHeaderId


if TYPE_CHECKING:
    from slither.analyses.data_flow.engine.analysis import Analysis
    from slither.core.cfg.node import Node
    from slither.core.declarations.function import Function


@dataclass(frozen=True, order=True)
class ControlFlowEdgeId:
    """Stable identity of one directed CFG edge."""

    source_id: int
    destination_id: int


@dataclass(frozen=True, order=True)
class LoopVariableId:
    """Static phi binding for one loop-carried source variable."""

    header_name: str
    entry_names: tuple[str, ...]
    back_names: tuple[str, ...]


@dataclass(frozen=True)
class NaturalLoop:
    """One dominator-defined natural-loop header and its incoming edges."""

    header_id: LoopHeaderId
    back_edges: frozenset[ControlFlowEdgeId]
    entry_edges: frozenset[ControlFlowEdgeId]


class LoopStructure:
    """Deterministic natural-loop classification for one function CFG."""

    def __init__(self, loops: tuple[NaturalLoop, ...] = ()) -> None:
        self._loops = {loop.header_id.node_id: loop for loop in loops}
        self._back_edges = frozenset(edge for loop in loops for edge in loop.back_edges)

    @classmethod
    def from_function(cls, function: Function) -> LoopStructure:
        """Classify an edge as back only when its destination dominates its source."""
        nodes = sorted(function.nodes, key=lambda node: node.node_id)
        back_by_header: dict[int, set[ControlFlowEdgeId]] = {}
        for source in nodes:
            for destination in sorted(source.sons, key=lambda node: node.node_id):
                if destination in source.dominators:
                    edge = ControlFlowEdgeId(source.node_id, destination.node_id)
                    back_by_header.setdefault(destination.node_id, set()).add(edge)
        by_id = {node.node_id: node for node in nodes}
        loops = tuple(
            cls._make_loop(by_id[header_id], edges)
            for header_id, edges in sorted(back_by_header.items())
        )
        return cls(loops)

    @staticmethod
    def _make_loop(header: Node, back_edges: set[ControlFlowEdgeId]) -> NaturalLoop:
        header_id = LoopHeaderId.from_node(header)
        entry_edges = frozenset(
            ControlFlowEdgeId(father.node_id, header.node_id)
            for father in header.fathers
            if ControlFlowEdgeId(father.node_id, header.node_id) not in back_edges
        )
        return NaturalLoop(header_id, frozenset(back_edges), entry_edges)

    @property
    def loops(self) -> tuple[NaturalLoop, ...]:
        """Return loops ordered by stable header identity."""
        return tuple(sorted(self._loops.values(), key=lambda loop: loop.header_id))

    def header(self, node_id: int) -> NaturalLoop | None:
        """Return natural-loop metadata for a header node ID."""
        return self._loops.get(node_id)

    def is_back_edge(self, edge: ControlFlowEdgeId) -> bool:
        """Return whether the edge closes a dominator-defined natural loop."""
        return edge in self._back_edges


@dataclass(frozen=True)
class LoopWideningContext:
    """Complete previous/current header states for one candidate generation."""

    header_id: LoopHeaderId
    generation: int
    previous_input: Domain
    current_input: Domain
    previous_output: Domain | None
    variables: tuple[LoopVariableId, ...]


@dataclass(frozen=True)
class LoopWideningResult:
    """One candidate header approximation and its generation-owned facts."""

    state: Domain
    generation_facts: tuple[Fact[object], ...] = ()


@dataclass(frozen=True)
class LoopUpdate:
    """Result of incorporating one incoming edge into a loop header."""

    changed: bool
    state: Domain | None = None


@dataclass
class LoopHeaderFixpoint:
    """Own incoming edge contributions and one live loop generation."""

    header_id: LoopHeaderId
    variables: tuple[LoopVariableId, ...]
    generation: int = 0
    previous_input: Domain | None = None
    current_input: Domain | None = None
    current_output: Domain | None = None
    _output_generation: int | None = None
    _entry_inputs: dict[ControlFlowEdgeId, Domain] = field(default_factory=dict)
    _back_inputs: dict[ControlFlowEdgeId, Domain] = field(default_factory=dict)
    _generation_facts: tuple[Fact[object], ...] = ()

    def update(
        self,
        edge: ControlFlowEdgeId,
        incoming: Domain,
        is_back_edge: bool,
        analysis: Analysis,
    ) -> LoopUpdate:
        """Join one edge contribution and advance only for a changed header state."""
        inputs = self._back_inputs if is_back_edge else self._entry_inputs
        if not self._update_input(inputs, edge, incoming):
            return LoopUpdate(False)
        candidate = self._combine_inputs()
        if self.current_input is None:
            initial = analysis.bottom_value()
            if not initial.join(candidate):
                return LoopUpdate(False)
            self.current_input = initial
            return LoopUpdate(True, initial.deep_copy())
        if not is_back_edge:
            return self._join_entry_candidate(candidate)
        if self._output_generation != self.generation:
            return self._update_pending_generation(candidate, analysis)
        return self._start_generation(candidate, analysis)

    def _start_generation(self, candidate: Domain, analysis: Analysis) -> LoopUpdate:
        """Start a generation from the latest transferred header state."""
        if self.current_input is None:
            raise RuntimeError("Loop generation started before tracker initialization")
        next_generation = self.generation + 1
        context = LoopWideningContext(
            self.header_id,
            next_generation,
            self.current_input.deep_copy(),
            candidate,
            self.current_output.deep_copy() if self.current_output is not None else None,
            self.variables,
        )
        result = analysis.apply_loop_widening(context)
        merged = self.current_input.deep_copy()
        if not merged.join(result.state):
            return LoopUpdate(False)
        self.previous_input = self.current_input.deep_copy()
        self.current_input = merged
        self.generation = next_generation
        self._generation_facts = result.generation_facts
        return LoopUpdate(True, merged.deep_copy())

    def _update_pending_generation(
        self,
        candidate: Domain,
        analysis: Analysis,
    ) -> LoopUpdate:
        """Join another latch into a generation whose header is already queued."""
        if self.previous_input is None or self.current_input is None:
            return LoopUpdate(False)
        context = LoopWideningContext(
            self.header_id,
            self.generation,
            self.previous_input.deep_copy(),
            candidate,
            self.current_output.deep_copy() if self.current_output is not None else None,
            self.variables,
        )
        result = analysis.apply_loop_widening(context)
        merged = self.previous_input.deep_copy()
        merged.join(result.state)
        expanded = self.current_input.deep_copy()
        if not expanded.join(merged):
            return LoopUpdate(False)
        self.current_input = expanded
        self._generation_facts = result.generation_facts
        return LoopUpdate(True, expanded.deep_copy())

    def _join_entry_candidate(self, candidate: Domain) -> LoopUpdate:
        if self.current_input is None:
            raise RuntimeError("Loop entry joined before tracker initialization")
        merged = self.current_input.deep_copy()
        if not merged.join(candidate):
            return LoopUpdate(False)
        if self._output_generation != self.generation:
            self.current_input = merged
            return LoopUpdate(True, merged.deep_copy())
        self.previous_input = self.current_input.deep_copy()
        self.current_input = merged
        self.generation += 1
        self._generation_facts = ()
        return LoopUpdate(True, merged.deep_copy())

    @staticmethod
    def _update_input(
        inputs: dict[ControlFlowEdgeId, Domain],
        edge: ControlFlowEdgeId,
        incoming: Domain,
    ) -> bool:
        existing = inputs.get(edge)
        if existing is None:
            inputs[edge] = incoming.deep_copy()
            return True
        return existing.join(incoming)

    def _combine_inputs(self) -> Domain:
        ordered = sorted((*self._entry_inputs.items(), *self._back_inputs.items()))
        if not ordered:
            raise RuntimeError("Loop header has no incoming contributions")
        combined = ordered[0][1].deep_copy()
        for _, incoming in ordered[1:]:
            combined.join(incoming)
        return combined

    def record_output(self, output: Domain) -> None:
        """Associate the latest complete header output with the current generation."""
        self.current_output = output.deep_copy()
        self._output_generation = self.generation

    @property
    def generation_fact_ids(self) -> frozenset[FactId]:
        """Return only the currently owned generation fact identities."""
        return frozenset(fact.fact_id for fact in self._generation_facts)

    @property
    def generation_facts(self) -> tuple[Fact[object], ...]:
        """Return the single live generation-owned fact set."""
        return self._generation_facts
