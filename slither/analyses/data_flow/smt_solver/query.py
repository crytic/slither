"""Backend-neutral ownership and lifecycle types for isolated SMT queries."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

from slither.analyses.data_flow.smt_solver.facts import (
    AnalysisContextId,
    EncodingId,
    Fact,
    FactId,
    FactOwnerKind,
    FactRegistry,
    SemanticStateId,
)


FormulaT = TypeVar("FormulaT")
SymbolT = TypeVar("SymbolT")


class QueryPurpose(Enum):
    """Semantic reason for materializing an isolated solver query."""

    FEASIBILITY = "feasibility"
    LOWER_BOUND = "lower_bound"
    UPPER_BOUND = "upper_bound"
    OVERFLOW = "overflow"
    UNDERFLOW = "underflow"
    REQUIRE = "require"
    ASSERT = "assert"
    PROPERTY = "property"


class FeasibilityStatus(Enum):
    """Outcome of an isolated satisfiability query."""

    SAT = "sat"
    UNSAT = "unsat"
    UNKNOWN = "unknown"
    TIMEOUT = "timeout"
    ERROR = "error"


class BoundStatus(Enum):
    """Provenance and outcome of one independently computed bound."""

    PROVEN = "proven"
    ABSTRACT = "abstract"
    UNKNOWN = "unknown"
    TIMEOUT = "timeout"
    ERROR = "error"
    NOT_ATTEMPTED = "not_attempted"


@dataclass(frozen=True)
class RangeInterval:
    """Closed integer interval used for explicit range fallbacks."""

    lower: int
    upper: int

    def to_dict(self) -> dict[str, int]:
        """Serialize the interval without losing integer precision."""
        return {"lower": self.lower, "upper": self.upper}


@dataclass(frozen=True)
class QueryMaterialization(Generic[FormulaT]):
    """Complete typed formula set for exactly one semantic query state."""

    encoding_id: EncodingId
    state_id: SemanticStateId
    purpose: QueryPurpose
    immutable_facts: tuple[Fact[FormulaT], ...]
    state_facts: tuple[Fact[FormulaT], ...]
    query_facts: tuple[Fact[FormulaT], ...]
    property_fact: Fact[FormulaT] | None = None

    def __post_init__(self) -> None:
        """Reject ownership mismatches before any backend sees a formula."""
        immutable_owners = {
            FactOwnerKind.IMMUTABLE_EQUATION,
            FactOwnerKind.CONTEXT_EQUATION,
        }
        if any(fact.fact_id.owner not in immutable_owners for fact in self.immutable_facts):
            raise ValueError("Function encoding contains a non-immutable fact")
        if any(fact.fact_id.owner is not FactOwnerKind.STATE_LOCAL for fact in self.state_facts):
            raise ValueError("State materialization accepts only STATE_LOCAL facts")
        if any(fact.fact_id.owner is not FactOwnerKind.QUERY_LOCAL for fact in self.query_facts):
            raise ValueError("Query materialization accepts only QUERY_LOCAL facts")
        state_fact_ids = frozenset(fact.fact_id for fact in self.state_facts)
        if state_fact_ids != self.state_id.active_fact_ids:
            raise ValueError("Materialized state facts do not match SemanticStateId")
        if (
            self.property_fact is not None
            and self.property_fact.fact_id.owner is not FactOwnerKind.PROPERTY_OBLIGATION
        ):
            raise ValueError("Selected property must be a PROPERTY_OBLIGATION fact")

    @property
    def facts(self) -> tuple[Fact[FormulaT], ...]:
        """Return all formulas in deterministic ownership order."""
        property_facts = (self.property_fact,) if self.property_fact is not None else ()
        return (*self.immutable_facts, *self.state_facts, *self.query_facts, *property_facts)


class FunctionEncoding(Generic[FormulaT, SymbolT]):
    """Reusable symbols and immutable equations for one function analysis."""

    def __init__(self, encoding_id: EncodingId | None = None) -> None:
        self._encoding_id = encoding_id or EncodingId("<unbound>", "<unbound>")
        self.symbols: dict[str, SymbolT] = {}
        self._facts: FactRegistry[FormulaT] = FactRegistry()

    @property
    def encoding_id(self) -> EncodingId:
        """Return the stable identity and version for this encoding."""
        return self._encoding_id

    @property
    def encoding_version(self) -> str:
        """Return the encoding schema version."""
        return self._encoding_id.encoding_version

    def bind(self, encoding_id: EncodingId) -> None:
        """Bind an empty unbound encoding to a function identity."""
        unbound = self._encoding_id.source_unit == self._encoding_id.function == "<unbound>"
        if self._encoding_id == encoding_id:
            return
        if not unbound or self.symbols or len(self._facts):
            raise RuntimeError("Cannot rebind a populated FunctionEncoding")
        self._encoding_id = encoding_id

    def register_fact(self, fact: Fact[FormulaT]) -> bool:
        """Register one immutable or context equation idempotently."""
        allowed = {
            FactOwnerKind.IMMUTABLE_EQUATION,
            FactOwnerKind.CONTEXT_EQUATION,
        }
        if fact.fact_id.owner not in allowed:
            raise ValueError("FunctionEncoding accepts only immutable or context equations")
        return self._facts.register(fact)

    def facts(self) -> tuple[Fact[FormulaT], ...]:
        """Return an immutable snapshot of reusable equations."""
        return self._facts.values()

    def fact_ids(self) -> frozenset[FactId]:
        """Return reusable fact identities for lifecycle checks."""
        return self._facts.ids()

    def clear(self) -> None:
        """Clear symbols and equations when the owning solver is reset."""
        self.symbols.clear()
        self._facts.clear()
        self._encoding_id = EncodingId("<unbound>", "<unbound>")


@dataclass(frozen=True)
class QuerySessionDiagnostics:
    """Immutable diagnostic record emitted when one session closes."""

    purpose: QueryPurpose
    encoding_id: EncodingId
    state_id: SemanticStateId
    timeout_ms: int
    elapsed_ms: float
    immutable_facts: int
    state_facts: int
    query_facts: int
    compatibility_query_facts: int
    property_materialized: bool
    assertion_copies: int
    feasibility_status: FeasibilityStatus | None = None
    bound_status: BoundStatus | None = None
    reason: str | None = None
    cleanup_balanced: bool = True

    def to_dict(self) -> dict[str, object]:
        """Serialize one session with stable textual status and owner identities."""
        return {
            "purpose": self.purpose.value,
            "encoding_id": repr(self.encoding_id),
            "state_id": repr(self.state_id),
            "timeout_ms": self.timeout_ms,
            "elapsed_ms": self.elapsed_ms,
            "immutable_facts": self.immutable_facts,
            "state_facts": self.state_facts,
            "query_facts": self.query_facts,
            "compatibility_query_facts": self.compatibility_query_facts,
            "property_materialized": self.property_materialized,
            "assertion_copies": self.assertion_copies,
            "feasibility_status": (
                self.feasibility_status.value if self.feasibility_status is not None else None
            ),
            "bound_status": self.bound_status.value if self.bound_status is not None else None,
            "reason": self.reason,
            "cleanup_balanced": self.cleanup_balanced,
        }


@dataclass(frozen=True)
class QueryDiagnostics:
    """Aggregate diagnostics for a public feasibility or range result."""

    sessions: tuple[QuerySessionDiagnostics, ...] = ()

    @property
    def elapsed_ms(self) -> float:
        """Return total backend time across all independent sessions."""
        return sum(session.elapsed_ms for session in self.sessions)

    @property
    def cleanup_balanced(self) -> bool:
        """Return whether every session restored persistent ownership state."""
        return all(session.cleanup_balanced for session in self.sessions)

    def to_dict(self) -> dict[str, object]:
        """Serialize all independent sessions for diagnostics and future caches."""
        return {
            "elapsed_ms": self.elapsed_ms,
            "cleanup_balanced": self.cleanup_balanced,
            "sessions": [session.to_dict() for session in self.sessions],
        }


@dataclass(frozen=True)
class FeasibilityResult:
    """Typed satisfiability result that preserves timeout and error distinctions."""

    status: FeasibilityStatus
    encoding_id: EncodingId
    state_id: SemanticStateId
    diagnostics: QueryDiagnostics

    def to_dict(self) -> dict[str, object]:
        """Serialize feasibility without collapsing timeout, unknown, or error."""
        return {
            "status": self.status.value,
            "encoding_id": repr(self.encoding_id),
            "state_id": repr(self.state_id),
            "diagnostics": self.diagnostics.to_dict(),
        }


@dataclass(frozen=True)
class RangeResult:
    """Independent lower/upper outcomes for one range query."""

    lower: int | None
    upper: int | None
    feasibility: FeasibilityStatus
    lower_status: BoundStatus
    upper_status: BoundStatus
    fallback_range: RangeInterval | None
    encoding_id: EncodingId
    state_id: SemanticStateId
    diagnostics: QueryDiagnostics

    def to_dict(self) -> dict[str, object]:
        """Serialize bound values and their distinct proof/fallback statuses."""
        return {
            "lower": self.lower,
            "upper": self.upper,
            "feasibility": self.feasibility.value,
            "lower_status": self.lower_status.value,
            "upper_status": self.upper_status.value,
            "fallback_range": (
                self.fallback_range.to_dict() if self.fallback_range is not None else None
            ),
            "encoding_id": repr(self.encoding_id),
            "state_id": repr(self.state_id),
            "diagnostics": self.diagnostics.to_dict(),
        }


class QuerySession(Generic[FormulaT]):
    """Disposable owner of one materialization and one backend instance."""

    def __init__(
        self,
        materialization: QueryMaterialization[FormulaT],
        timeout_ms: int,
        compatibility_query_facts: int,
        cleanup: Callable[[], bool],
    ) -> None:
        self.materialization = materialization
        self.timeout_ms = timeout_ms
        self.compatibility_query_facts = compatibility_query_facts
        self.backend: object | None = None
        self._cleanup = cleanup
        self._started = time.perf_counter()
        self._closed = False
        self._diagnostics: QuerySessionDiagnostics | None = None
        self._record_created()

    def attach_backend(self, backend: object) -> None:
        """Transfer ownership of a newly created backend instance to this session."""
        if self._closed or self.backend is not None:
            raise RuntimeError("QuerySession backend ownership is already settled")
        self.backend = backend

    def close(
        self,
        *,
        feasibility_status: FeasibilityStatus | None = None,
        bound_status: BoundStatus | None = None,
        reason: str | None = None,
    ) -> QuerySessionDiagnostics:
        """Dispose backend state and validate the persistent ownership snapshot."""
        if self._closed:
            if self._diagnostics is None:
                raise RuntimeError("Closed QuerySession has no diagnostics")
            return self._diagnostics
        self.backend = None
        cleanup_balanced = self._cleanup()
        elapsed_ms = (time.perf_counter() - self._started) * 1000
        materialization = self.materialization
        self._diagnostics = QuerySessionDiagnostics(
            purpose=materialization.purpose,
            encoding_id=materialization.encoding_id,
            state_id=materialization.state_id,
            timeout_ms=self.timeout_ms,
            elapsed_ms=elapsed_ms,
            immutable_facts=len(materialization.immutable_facts),
            state_facts=len(materialization.state_facts),
            query_facts=len(materialization.query_facts),
            compatibility_query_facts=self.compatibility_query_facts,
            property_materialized=materialization.property_fact is not None,
            assertion_copies=len(materialization.facts),
            feasibility_status=feasibility_status,
            bound_status=bound_status,
            reason=reason,
            cleanup_balanced=cleanup_balanced,
        )
        self._closed = True
        self._record_closed(self._diagnostics)
        return self._diagnostics

    @property
    def diagnostics(self) -> QuerySessionDiagnostics:
        """Return close diagnostics after the session has been disposed."""
        if self._diagnostics is None:
            raise RuntimeError("QuerySession diagnostics are unavailable before close")
        return self._diagnostics

    def __enter__(self) -> QuerySession[FormulaT]:
        """Enter this owned query scope."""
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        """Guarantee cleanup if a query path raises before explicit close."""
        del exc_type, traceback
        if not self._closed:
            reason = (
                f"{type(exc).__name__}: {exc}"
                if exc is not None
                else "session closed without result"
            )
            bound_purposes = {QueryPurpose.LOWER_BOUND, QueryPurpose.UPPER_BOUND}
            if self.materialization.purpose in bound_purposes:
                self.close(bound_status=BoundStatus.ERROR, reason=reason)
            else:
                self.close(feasibility_status=FeasibilityStatus.ERROR, reason=reason)

    def _record_created(self) -> None:
        """Forward session creation to optional telemetry."""
        from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry

        telemetry = get_telemetry()
        if telemetry is not None and telemetry.enabled:
            telemetry.record_query_session_created(
                self.materialization,
                self.timeout_ms,
                self.compatibility_query_facts,
            )

    @staticmethod
    def _record_closed(diagnostics: QuerySessionDiagnostics) -> None:
        """Forward final session diagnostics to optional telemetry."""
        from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry

        telemetry = get_telemetry()
        if telemetry is not None and telemetry.enabled:
            telemetry.record_query_session_closed(diagnostics)


def empty_state_id(encoding_id: EncodingId) -> SemanticStateId:
    """Create the explicit empty state used by source-compatible raw queries."""
    return SemanticStateId(
        reachability="query",
        context_id=AnalysisContextId(encoding_id),
        abstract_values=(),
        active_fact_ids=frozenset(),
        storage_summary=(),
        comparisons=(),
        dependencies=(),
    )
