"""Interprocedural extension point for data flow analyses.

Adds call handling on top of the intraprocedural engine: for each
resolvable callee, a real nested Engine fixpoint runs over the callee's
CFG, seeded with caller argument bindings via ``Engine.new``'s
``entry_domain`` hook. Concrete analyses supply two domain-specific
hooks (``bind_arguments``, ``extract_return_summary``); everything else
(recursion guarding, depth capping, call-site attribution) is generic.

``resolve_callee`` and ``iter_matching_unpacks`` live here in the engine
layer rather than in a shared SlithIR utility: their contracts
(per-operation-type body checks, lvalue filtering) exist to serve
interprocedural data-flow analyses, not general IR consumers.
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from collections.abc import Iterator
from typing import Generic, TypeVar

from slither.analyses.data_flow.engine.analysis import Analysis, AnalysisState
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.engine.engine import Engine
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.call import Call
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.unpack import Unpack
from slither.slithir.variables.tuple import TupleVariable

logger = logging.getLogger("DataFlow")

SummaryT = TypeVar("SummaryT")


class InterproceduralAnalysis(Analysis, Generic[SummaryT]):
    """Base class for data flow analyses that follow calls into callees.

    Subclasses implement ``bind_arguments`` (map call-site argument
    state to a callee entry domain) and ``extract_return_summary``
    (reduce the callee's fixpoint results to a summary of type
    ``SummaryT``); ``analyze_call`` provides the machinery in between.
    A single per-instance call stack guards against recursion across
    all call operation types, and a parallel call-site stack lets
    findings raised inside callee bodies be attributed to the
    user-visible (outermost) call site via ``outermost_call_site``.

    Warning:
        ``Engine.new`` calls ``analysis.prepare_for_function(callee)``
        on the SAME analysis instance mid-run of the caller's engine
        (see ``Engine.new``). Any per-function state cached there is
        clobbered and NOT restored when the nested engine finishes.
        Interprocedural analyses must keep ``prepare_for_function``
        re-entrant or stateless.
    """

    # Companion to Engine._MAX_ITERATIONS, which is per engine instance
    # and does not bound total work: a call inside a loop body re-runs
    # the callee engine on every worklist revisit of that node
    # (k revisits x d nesting levels => k^d callee runs), and nested
    # engines recurse through Python frames (~10 per level; the default
    # recursion limit of 1000 would surface as an opaque RecursionError
    # near depth ~100). Cap at 32 and treat a hit like recursion.
    _MAX_CALL_DEPTH = 32

    def __init__(self) -> None:
        """Initialize the per-instance call and call-site stacks."""
        self._call_stack: list[Function] = []
        self._call_site_stack: list[Node] = []

    @abstractmethod
    def bind_arguments(
        self,
        callee: Function,
        arguments: list[Variable],
        caller_domain: Domain,
    ) -> Domain:
        """Build the callee's entry domain from call-site arguments.

        Args:
            callee: The function about to be analyzed.
            arguments: Call-site argument variables, positionally
                matching ``callee.parameters``.
            caller_domain: The caller's abstract state at the call
                site, read-only from this method's perspective.

        Returns:
            A fresh domain seeding the callee's entry pre-state. The
            engine joins it into a fresh bottom value, so ownership of
            the returned object is not shared with the caller.
        """

    @abstractmethod
    def extract_return_summary(
        self,
        callee: Function,
        results: dict[Node, AnalysisState[Analysis]],
    ) -> SummaryT | None:
        """Summarize the callee's fixpoint results for the call site.

        Summaries are a typed ``SummaryT`` rather than a ``Domain``
        because a call-site summary is not a lattice element: it can
        carry provenance traces, per-index tuple results, and control
        flags (e.g. a recursion marker) that have no join semantics.

        Args:
            callee: The function that was analyzed.
            results: Per-node pre/post states from ``Engine.result()``.

        Returns:
            A domain-specific summary of the callee's return values,
            or None if no summary could be extracted.
        """

    def on_recursion(self, callee: Function) -> SummaryT | None:
        """Summary to use when the callee is already on the stack.

        Also used when the call depth cap is hit. Override to return a
        conservative summary; the default gives up with None.

        Args:
            callee: The function whose analysis was skipped.

        Returns:
            A conservative summary, or None.
        """
        return None

    # Memoization decision: no (function, argument-summary) -> summary
    # cache, and no __eq__/__hash__ added to Domain. Caching is a pure
    # performance feature — termination is already guaranteed by the
    # exact-recursion guard plus the depth cap — and the right cache
    # key is a domain-specific projection (e.g. a tuple of parameter
    # TagSets), not whole-Domain equality. If profiling ever demands
    # it, add an optional call_summary_key() hook returning
    # Hashable | None — an additive change. Do not build it now.
    def analyze_call(
        self,
        callee: Function,
        arguments: list[Variable],
        caller_domain: Domain,
        call_site: Node,
    ) -> SummaryT | None:
        """Run a nested engine fixpoint over the callee and summarize it.

        Args:
            callee: The called function to analyze.
            arguments: Call-site argument variables, positionally
                matching ``callee.parameters``.
            caller_domain: The caller's abstract state at the call site.
            call_site: The caller's CFG node containing the call.

        Returns:
            The summary from ``extract_return_summary``; the
            ``on_recursion`` summary when the callee is already being
            analyzed or the depth cap is hit; None when the callee has
            no body. Callers that must distinguish recursion from a
            missing body should check ``is_on_call_stack`` first.
        """
        if not callee.nodes:
            logger.debug("Function %s has no body nodes, skipping analysis", callee.name)
            return None

        if self.is_on_call_stack(callee):
            logger.debug("Recursion guard: %s already on call stack", callee.name)
            return self.on_recursion(callee)

        if len(self._call_stack) >= self._MAX_CALL_DEPTH:
            chain = " -> ".join(function.name for function in self._call_stack)
            logger.warning(
                "Call depth cap (%d) hit at %s, treating as recursion. Chain: %s",
                self._MAX_CALL_DEPTH,
                callee.name,
                chain,
            )
            return self.on_recursion(callee)

        entry_domain = self.bind_arguments(callee, arguments, caller_domain)

        self._call_stack.append(callee)
        self._call_site_stack.append(call_site)
        try:
            engine: Engine[Analysis] = Engine.new(self, callee, entry_domain=entry_domain)
            engine.run_analysis()
        finally:
            self._call_stack.pop()
            self._call_site_stack.pop()

        return self.extract_return_summary(callee, engine.result())

    def is_on_call_stack(self, callee: Function) -> bool:
        """Check whether a function is currently being analyzed.

        Args:
            callee: The function to look for on the call stack.

        Returns:
            True if the function is on the active call stack.
        """
        return callee in self._call_stack

    def outermost_call_site(self) -> Node | None:
        """Return the user-visible call site for finding attribution.

        Returns:
            The bottom-of-stack caller node (the call the user wrote in
            the outermost function under analysis), or None when no
            interprocedural analysis is active.
        """
        return self._call_site_stack[0] if self._call_site_stack else None


def resolve_callee(operation: Call) -> Function | None:
    """Resolve the Function targeted by a call operation.

    Resolution semantics are deliberately per-operation-type:

    - ``LibraryCall``: the target Function with no body check —
      libraries are compiled with the contract. Checked before
      ``HighLevelCall`` because ``LibraryCall`` subclasses it.
    - ``HighLevelCall``: the target Function only when it has body
      nodes. Interface functions have no implementation and resolve to
      None so callers take name-based fallback paths instead of an
      exact (interface-contract, function) match.
    - ``InternalCall``: the target Function with no body check.
    - Any other Call subtype, or a non-Function target: None.

    Args:
        operation: The call operation to resolve.

    Returns:
        The callee Function, or None per the rules above.
    """
    if isinstance(operation, InternalCall):
        called_function = operation.function
        if isinstance(called_function, Function):
            return called_function
        return None
    if isinstance(operation, LibraryCall):
        called_function = operation.function
        if isinstance(called_function, Function):
            return called_function
        return None
    if isinstance(operation, HighLevelCall):
        called_function = operation.function
        if not isinstance(called_function, Function):
            return None
        if not called_function.nodes:
            return None
        return called_function
    return None


def iter_matching_unpacks(node: Node, tuple_variable: TupleVariable) -> Iterator[Unpack]:
    """Yield the node's Unpack operations reading a given tuple variable.

    Used when a call returns a tuple: the per-index results are applied
    to the Unpack destinations found in the same node.

    Args:
        node: The CFG node containing the tuple-returning call.
        tuple_variable: The call's TupleVariable lvalue.

    Yields:
        Unpack operations whose tuple equals ``tuple_variable`` and
        whose lvalue is set.
    """
    for operation in node.irs_ssa:
        if not isinstance(operation, Unpack):
            continue
        if operation.tuple != tuple_variable:
            continue
        if operation.lvalue is None:
            continue
        yield operation
