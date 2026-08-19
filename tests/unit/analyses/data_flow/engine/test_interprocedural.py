"""Unit tests for the interprocedural analysis extension point.

The code under test never isinstance-checks Function or Node inside
``InterproceduralAnalysis`` or ``iter_matching_unpacks``, so lightweight
stand-ins cover those slither-core boundaries; the analysis, domain, and
direction used here are real implementations, so the nested Engine
fixpoint machinery is exercised, not mocked. ``resolve_callee`` does
isinstance-check its operation and target, so those tests build real
SlithIR operations and a real (minimal) ``Function`` subclass.

The record collector attaches to the ``DataFlow`` logger directly instead
of using ``caplog``: the end-to-end data-flow suite sets
``propagate = False`` for the whole session, so anything relying on
propagation here would break depending on test order.
"""

from __future__ import annotations

import logging
from collections import deque
from collections.abc import Iterator

import pytest

from slither.analyses.data_flow.engine.analysis import Analysis, AnalysisState
from slither.analyses.data_flow.engine.direction import Direction
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.engine.interprocedural import (
    InterproceduralAnalysis,
    iter_matching_unpacks,
    resolve_callee,
)
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.variables.local_variable import LocalVariable
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.operations.unpack import Unpack
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.tuple import TupleVariable

LOGGER_NAME = "DataFlow"


class _FakeCompilationUnit:
    """The one attribute Function.__init__ reads."""

    is_solidity = True


class _FakeNode:
    """CFG node stand-in: the engine only needs node_id, hashed by identity."""

    def __init__(self, name: str, node_id: int = 0) -> None:
        self.name = name
        self.node_id = node_id
        self.irs_ssa: list = []

    def __repr__(self) -> str:
        return f"<node {self.name}>"


class _StubFunction(Function):
    """Concrete Function overriding only what instantiation requires."""

    def __init__(self, name: str) -> None:
        super().__init__(_FakeCompilationUnit())
        self.name = name

    @property
    def canonical_name(self) -> str:
        return self._name or ""

    @property
    def file_scope(self) -> None:
        return None

    @property
    def functions_shadowed(self) -> list[Function]:
        return []

    def get_summary(self) -> tuple:
        return ("", "", "", [], [], [], [], [])

    def generate_slithir_ssa(self, all_ssa_state_variables_instances) -> None:
        return None


def _function_with_body(name: str) -> tuple[_StubFunction, _FakeNode]:
    function = _StubFunction(name)
    node = _FakeNode(f"{name}:entry")
    function.nodes = [node]
    function.entry_point = node
    return function, node


def _bodyless_function(name: str) -> _StubFunction:
    return _StubFunction(name)


class _SetDomain(Domain):
    """Powerset-of-strings lattice; join is set union."""

    def __init__(self, values: set[str] | None = None) -> None:
        self.values: set[str] = set(values or ())

    @classmethod
    def top(cls) -> _SetDomain:
        return cls({"<top>"})

    @classmethod
    def bottom(cls) -> _SetDomain:
        return cls()

    def join(self, other: Domain) -> bool:
        assert isinstance(other, _SetDomain)
        before = len(self.values)
        self.values |= other.values
        return len(self.values) != before

    def copy(self) -> _SetDomain:
        return _SetDomain(self.values)


class _ScriptedDirection(Direction):
    """Forward direction that follows the analysis's scripted call plan.

    Mimics what a real transfer function does at a call site: it invokes
    ``analyze_call`` mid-run of the enclosing engine.
    """

    @property
    def IS_FORWARD(self) -> bool:
        return True

    def apply_transfer_function(
        self,
        analysis: Analysis,
        current_state: AnalysisState,
        node: _FakeNode,
        worklist: deque,
        global_state: dict,
    ) -> None:
        assert isinstance(analysis, _ScriptedAnalysis)
        current_state.post = current_state.pre.copy()
        analysis.stack_snapshots.append(
            (
                node,
                [fn for fn in analysis.watched if analysis.is_on_call_stack(fn)],
                analysis.outermost_call_site(),
            )
        )
        if node in analysis.raise_at:
            raise RuntimeError(f"transfer failure at {node.name}")
        plan = analysis.call_plan.get(node)
        if plan is not None:
            callee, arguments = plan
            analysis.summaries[node] = analysis.analyze_call(
                callee, arguments, current_state.post, node
            )


class _ScriptedAnalysis(InterproceduralAnalysis[str]):
    """Interprocedural analysis whose call graph is scripted per node.

    ``call_plan`` maps a CFG node to a (callee, arguments) pair; when the
    engine processes that node the direction calls ``analyze_call``.
    Keeps the base class's default ``on_recursion``.
    """

    def __init__(self) -> None:
        super().__init__()
        self.call_plan: dict[_FakeNode, tuple[Function, list]] = {}
        self.raise_at: list[_FakeNode] = []
        self.watched: list[Function] = []
        self.engines_run: list[Function] = []
        self.bound: list[tuple[Function, list, Domain]] = []
        self.extracted: list[Function] = []
        self.extract_results: dict[Function, dict] = {}
        self.summaries: dict[_FakeNode, str | None] = {}
        self.stack_snapshots: list[tuple[_FakeNode, list[Function], object]] = []

    def domain(self) -> Domain:
        return _SetDomain()

    def direction(self) -> Direction:
        return _ScriptedDirection()

    def bottom_value(self) -> Domain:
        return _SetDomain.bottom()

    def transfer_function(self, node, domain, operation) -> None:
        """Unused; _ScriptedDirection drives node processing directly."""

    def prepare_for_function(self, function: Function) -> None:
        self.engines_run.append(function)

    def bind_arguments(self, callee, arguments, caller_domain) -> Domain:
        self.bound.append((callee, list(arguments), caller_domain))
        return _SetDomain({f"param:{callee.name}"})

    def extract_return_summary(self, callee, results) -> str:
        self.extracted.append(callee)
        self.extract_results[callee] = results
        return f"summary:{callee.name}"


class _SentinelAnalysis(_ScriptedAnalysis):
    """Overrides on_recursion with an observable sentinel summary."""

    def __init__(self) -> None:
        super().__init__()
        self.recursion_hits: list[Function] = []

    def on_recursion(self, callee: Function) -> str:
        self.recursion_hits.append(callee)
        return f"recursed:{callee.name}"


class _RecordCollector(logging.Handler):
    """Handler that keeps every record it is given."""

    def __init__(self) -> None:
        super().__init__(level=logging.NOTSET)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.fixture(name="dataflow_records")
def fixture_dataflow_records() -> Iterator[list[logging.LogRecord]]:
    """Collect DataFlow log records regardless of propagation settings."""
    logger = logging.getLogger(LOGGER_NAME)
    previous_level = logger.level
    handler = _RecordCollector()
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    try:
        yield handler.records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)


def _internal_call() -> InternalCall:
    return InternalCall(("target", "C"), 0, None, "")


def _high_level_call() -> HighLevelCall:
    return HighLevelCall(LocalVariable(), Constant("target"), 0, None, "")


def _library_call() -> LibraryCall:
    library = Contract(_FakeCompilationUnit(), None)
    library.name = "Lib"
    return LibraryCall(library, Constant("target"), 0, None, "")


def _local(name: str) -> LocalVariable:
    variable = LocalVariable()
    variable.name = name
    return variable


# ---------------------------------------------------------------------------
# analyze_call machinery
# ---------------------------------------------------------------------------


def test_analyze_call_runs_nested_engine_and_returns_summary() -> None:
    analysis = _ScriptedAnalysis()
    callee, _ = _function_with_body("callee")
    argument = _local("amount")
    caller_domain = _SetDomain({"caller-state"})

    summary = analysis.analyze_call(callee, [argument], caller_domain, _FakeNode("site"))

    assert summary == "summary:callee"
    assert analysis.engines_run == [callee]
    assert analysis.bound == [(callee, [argument], caller_domain)]
    assert analysis.extracted == [callee]


def test_bound_entry_domain_seeds_the_nested_engine() -> None:
    """The domain built by bind_arguments reaches the callee's entry state."""
    analysis = _ScriptedAnalysis()
    callee, callee_node = _function_with_body("callee")

    analysis.analyze_call(callee, [], _SetDomain(), _FakeNode("site"))

    entry_state = analysis.extract_results[callee][callee_node]
    assert "param:callee" in entry_state.pre.values
    assert "param:callee" in entry_state.post.values


def test_no_body_callee_returns_none_without_on_recursion() -> None:
    """No-body and recursion must stay distinguishable outcomes."""
    analysis = _SentinelAnalysis()
    callee = _bodyless_function("iface_fn")

    result = analysis.analyze_call(callee, [], _SetDomain(), _FakeNode("site"))

    assert result is None
    assert analysis.recursion_hits == []
    assert analysis.bound == []
    assert analysis.engines_run == []


# ---------------------------------------------------------------------------
# Recursion guard and depth cap
# ---------------------------------------------------------------------------


def test_direct_recursion_uses_on_recursion_and_analyzes_body_once() -> None:
    analysis = _SentinelAnalysis()
    function, node = _function_with_body("selfcall")
    analysis.call_plan[node] = (function, [])

    summary = analysis.analyze_call(function, [], _SetDomain(), _FakeNode("root"))

    assert summary == "summary:selfcall"
    assert analysis.engines_run == [function]
    assert analysis.recursion_hits == [function]
    assert analysis.summaries[node] == "recursed:selfcall"


def test_direct_recursion_default_on_recursion_returns_none() -> None:
    analysis = _ScriptedAnalysis()
    function, node = _function_with_body("selfcall")
    analysis.call_plan[node] = (function, [])

    summary = analysis.analyze_call(function, [], _SetDomain(), _FakeNode("root"))

    assert summary == "summary:selfcall"
    assert analysis.summaries[node] is None
    assert analysis.engines_run == [function]


def test_mutual_recursion_caught_by_one_stack_across_op_types() -> None:
    """A cycle spanning InternalCall and HighLevelCall is caught on the
    first re-entry: the guard is one per-analysis stack, not per op type."""
    analysis = _SentinelAnalysis()
    fn_a, node_a = _function_with_body("a")
    fn_b, node_b = _function_with_body("b")

    a_to_b = _internal_call()
    a_to_b.function = fn_b
    b_to_a = _high_level_call()
    b_to_a.function = fn_a
    analysis.call_plan[node_a] = (resolve_callee(a_to_b), [])
    analysis.call_plan[node_b] = (resolve_callee(b_to_a), [])

    summary = analysis.analyze_call(fn_a, [], _SetDomain(), _FakeNode("root"))

    assert summary == "summary:a"
    assert analysis.engines_run == [fn_a, fn_b]
    assert analysis.recursion_hits == [fn_a]
    assert analysis.summaries[node_a] == "summary:b"
    assert analysis.summaries[node_b] == "recursed:a"
    assert analysis.extracted == [fn_b, fn_a]


def test_depth_cap_blocks_exactly_at_max_call_depth(
    dataflow_records: list[logging.LogRecord],
) -> None:
    """A chain reaching _MAX_CALL_DEPTH is fully analyzed; the next frame
    is treated as recursion, before bind_arguments runs, with a warning."""
    depth = InterproceduralAnalysis._MAX_CALL_DEPTH
    analysis = _SentinelAnalysis()
    functions = []
    nodes = []
    for index in range(depth + 1):
        function, node = _function_with_body(f"f{index}")
        functions.append(function)
        nodes.append(node)
    for index in range(depth):
        analysis.call_plan[nodes[index]] = (functions[index + 1], [])

    summary = analysis.analyze_call(functions[0], [], _SetDomain(), _FakeNode("root"))

    assert summary == "summary:f0"
    assert analysis.engines_run == functions[:depth]
    assert analysis.recursion_hits == [functions[depth]]
    assert analysis.summaries[nodes[depth - 1]] == f"recursed:f{depth}"
    for index in range(depth - 1):
        assert analysis.summaries[nodes[index]] == f"summary:f{index + 1}"
    assert [entry[0] for entry in analysis.bound] == functions[:depth]

    warnings = [record for record in dataflow_records if record.levelno == logging.WARNING]
    assert len(warnings) == 1
    message = warnings[0].getMessage()
    assert f"Call depth cap ({depth}) hit at f{depth}" in message
    assert "f0 -> f1" in message


# ---------------------------------------------------------------------------
# Call and call-site stacks
# ---------------------------------------------------------------------------


def test_stacks_empty_before_and_after_a_successful_run() -> None:
    analysis = _ScriptedAnalysis()
    fn_a, node_a = _function_with_body("a")
    fn_b, _node_b = _function_with_body("b")
    analysis.call_plan[node_a] = (fn_b, [])

    assert analysis.is_on_call_stack(fn_a) is False
    assert analysis.outermost_call_site() is None

    analysis.analyze_call(fn_a, [], _SetDomain(), _FakeNode("root"))

    assert analysis.is_on_call_stack(fn_a) is False
    assert analysis.is_on_call_stack(fn_b) is False
    assert analysis.outermost_call_site() is None


def test_outermost_call_site_is_bottom_of_stack_during_nested_run() -> None:
    analysis = _ScriptedAnalysis()
    fn_a, node_a = _function_with_body("a")
    fn_b, node_b = _function_with_body("b")
    analysis.call_plan[node_a] = (fn_b, [])
    analysis.watched = [fn_a, fn_b]
    root_site = _FakeNode("root")

    analysis.analyze_call(fn_a, [], _SetDomain(), root_site)

    snapshots = {node: (on_stack, site) for node, on_stack, site in analysis.stack_snapshots}
    assert snapshots[node_a] == ([fn_a], root_site)
    assert snapshots[node_b] == ([fn_a, fn_b], root_site)


def test_stacks_are_popped_when_a_nested_engine_raises() -> None:
    analysis = _ScriptedAnalysis()
    fn_a, node_a = _function_with_body("a")
    fn_b, node_b = _function_with_body("b")
    analysis.call_plan[node_a] = (fn_b, [])
    analysis.raise_at.append(node_b)

    with pytest.raises(RuntimeError, match="transfer failure at b:entry"):
        analysis.analyze_call(fn_a, [], _SetDomain(), _FakeNode("root"))

    assert analysis.is_on_call_stack(fn_a) is False
    assert analysis.is_on_call_stack(fn_b) is False
    assert analysis.outermost_call_site() is None
    assert analysis._call_stack == []
    assert analysis._call_site_stack == []


# ---------------------------------------------------------------------------
# resolve_callee
# ---------------------------------------------------------------------------


def test_resolve_internal_call_returns_function_without_body_check() -> None:
    bodyless = _bodyless_function("target")
    operation = _internal_call()
    operation.function = bodyless

    assert resolve_callee(operation) is bodyless


def test_resolve_internal_call_non_function_target_is_none() -> None:
    operation = _internal_call()
    assert resolve_callee(operation) is None

    operation.function = _local("not_a_function")
    assert resolve_callee(operation) is None


def test_resolve_library_call_returns_function_without_body_check() -> None:
    """LibraryCall subclasses HighLevelCall: a bodyless library target must
    still resolve, i.e. the LibraryCall branch must win over HighLevelCall."""
    bodyless = _bodyless_function("target")
    operation = _library_call()
    operation.function = bodyless

    assert resolve_callee(operation) is bodyless


def test_resolve_library_call_non_function_target_is_none() -> None:
    operation = _library_call()
    assert resolve_callee(operation) is None


def test_resolve_high_level_call_with_body_returns_function() -> None:
    implemented, _ = _function_with_body("impl")
    operation = _high_level_call()
    operation.function = implemented

    assert resolve_callee(operation) is implemented


def test_resolve_high_level_call_bodyless_target_is_none() -> None:
    """Interface targets must resolve to None so callers fall back to
    name-based lookups instead of an exact (interface, function) match."""
    bodyless = _bodyless_function("iface_fn")
    operation = _high_level_call()
    operation.function = bodyless

    assert resolve_callee(operation) is None


def test_resolve_high_level_call_non_function_target_is_none() -> None:
    operation = _high_level_call()
    assert resolve_callee(operation) is None

    operation.function = _local("not_a_function")
    assert resolve_callee(operation) is None


def test_resolve_unrelated_call_subtype_is_none() -> None:
    operation = SolidityCall(SolidityFunction("revert()"), 0, None, "")
    assert resolve_callee(operation) is None


# ---------------------------------------------------------------------------
# iter_matching_unpacks
# ---------------------------------------------------------------------------


def _tuple_variable(index: int) -> TupleVariable:
    return TupleVariable(_FakeNode("tuple_origin"), index=index)


def test_iter_matching_unpacks_filters_and_preserves_order() -> None:
    target = _tuple_variable(0)
    other = _tuple_variable(1)

    first = Unpack(_local("a"), target, 0)
    wrong_tuple = Unpack(_local("b"), other, 0)
    cleared = Unpack(_local("c"), target, 1)
    cleared.lvalue = None
    second = Unpack(_local("d"), target, 2)
    not_an_unpack = _internal_call()

    node = _FakeNode("call_site")
    node.irs_ssa = [first, wrong_tuple, not_an_unpack, cleared, second]

    assert list(iter_matching_unpacks(node, target)) == [first, second]


def test_iter_matching_unpacks_empty_node_yields_nothing() -> None:
    node = _FakeNode("call_site")
    assert list(iter_matching_unpacks(node, _tuple_variable(0))) == []
