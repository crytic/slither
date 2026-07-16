"""Backend-neutral identities and ownership metadata for analysis facts."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Generic, TypeVar


class FactOwnerKind(Enum):
    """Lifetime owner for an analysis fact."""

    IMMUTABLE_EQUATION = "immutable_equation"
    CONTEXT_EQUATION = "context_equation"
    STATE_LOCAL = "state_local"
    LOOP_GENERATION = "loop_generation"
    QUERY_LOCAL = "query_local"
    PROPERTY_OBLIGATION = "property_obligation"
    UNCLASSIFIED_COMPATIBILITY = "unclassified_compatibility"


class FactKind(Enum):
    """Semantic role of a fact, independent of its concrete formula."""

    EQUATION = "equation"
    VALUE_BINDING = "value_binding"
    PATH_CONDITION = "path_condition"
    BRANCH_GUARD = "branch_guard"
    CHECKED_ARITHMETIC = "checked_arithmetic"
    NONZERO_REQUIREMENT = "nonzero_requirement"
    RANGE_BOUND = "range_bound"
    QUERY_ASSUMPTION = "query_assumption"
    PROPERTY = "property"
    COMPATIBILITY = "compatibility"


class FactOriginKind(Enum):
    """Static source from which a fact was derived."""

    OPERATION = "operation"
    CFG_EDGE = "cfg_edge"
    FUNCTION_ENTRY = "function_entry"
    CALL_BINDING = "call_binding"
    STORAGE = "storage"
    LOOP = "loop"
    ABSTRACT_STATE = "abstract_state"
    QUERY = "query"
    PROPERTY = "property"
    COMPATIBILITY = "compatibility"


@dataclass(frozen=True, order=True)
class EncodingId:
    """Identity of the static function encoding that declares symbols."""

    source_unit: str
    function: str
    encoding_version: str = "interval-v1"

    @classmethod
    def from_function(cls, function: object) -> EncodingId:
        """Build a deterministic encoding identity from a Slither function."""
        function_name = str(getattr(function, "canonical_name", function))
        source_mapping = getattr(function, "source_mapping", None)
        filename = getattr(source_mapping, "filename", None)
        source_unit = getattr(filename, "relative", None)
        if not source_unit:
            source_unit = getattr(filename, "short", None)
        return cls(source_unit=str(source_unit or "<unknown-source>"), function=function_name)


@dataclass(frozen=True, order=True)
class StaticOperationId:
    """Traversal-independent identity of one operation in a static CFG."""

    encoding_id: EncodingId
    node_id: int
    ir_position: int

    @classmethod
    def from_operation(cls, operation: object, node: object) -> StaticOperationId:
        """Identify an operation by function, CFG node, and static IR position."""
        operations = getattr(node, "irs_ssa", ()) or ()
        position = next(
            (index for index, candidate in enumerate(operations) if candidate is operation),
            None,
        )
        if position is None:
            raise ValueError("Operation is not present in the node's static SSA operation list")
        function = getattr(node, "function", None)
        if function is None:
            raise ValueError("CFG node has no function for deterministic operation identity")
        return cls(
            encoding_id=EncodingId.from_function(function),
            node_id=int(node.node_id),
            ir_position=position,
        )

    @classmethod
    def synthetic(cls, node: object, ir_position: int = -1) -> StaticOperationId:
        """Identify a deterministic synthetic transfer associated with a CFG node."""
        function = getattr(node, "function", None)
        if function is None:
            raise ValueError("CFG node has no function for deterministic operation identity")
        return cls(
            encoding_id=EncodingId.from_function(function),
            node_id=int(node.node_id),
            ir_position=ir_position,
        )


@dataclass(frozen=True)
class AnalysisContextId:
    """Identity of a function encoding instantiated in an analysis context."""

    encoding_id: EncodingId
    call_path: tuple[StaticOperationId, ...] = ()
    storage_path: tuple[str, ...] = ()
    summary_path: tuple[str, ...] = ()

    @classmethod
    def root(cls, function: object) -> AnalysisContextId:
        """Create the root context for a function analysis."""
        return cls(encoding_id=EncodingId.from_function(function))

    @classmethod
    def unbound(cls) -> AnalysisContextId:
        """Create an explicit context for state constructed before function binding."""
        return cls(encoding_id=EncodingId("<unbound>", "<unbound>"))

    def for_call(
        self,
        called_function: object,
        call_operation_id: StaticOperationId,
    ) -> AnalysisContextId:
        """Create a callee context without deriving identity from symbol names."""
        return AnalysisContextId(
            encoding_id=EncodingId.from_function(called_function),
            call_path=(*self.call_path, call_operation_id),
            storage_path=self.storage_path,
            summary_path=self.summary_path,
        )

    def for_storage(self, slot_key: str) -> AnalysisContextId:
        """Create a storage-sensitive child context for one slot."""
        return replace(self, storage_path=(*self.storage_path, slot_key))

    def telemetry_key(self) -> str:
        """Return a readable stable key for telemetry grouping only."""
        encoding = self._encoding_telemetry_key(self.encoding_id)
        calls = "/".join(
            f"{self._encoding_telemetry_key(item.encoding_id)}:{item.node_id}:{item.ir_position}"
            for item in self.call_path
        )
        storage = "/".join(self.storage_path)
        summary = "/".join(self.summary_path)
        return "|".join((encoding, calls, storage, summary))

    @staticmethod
    def _encoding_telemetry_key(encoding_id: EncodingId) -> str:
        """Render the complete encoding identity without defining its semantics."""
        return ":".join(
            (
                encoding_id.source_unit,
                encoding_id.function,
                encoding_id.encoding_version,
            )
        )


@dataclass(frozen=True)
class FactProvenance:
    """Origin and context needed to audit a fact's ownership."""

    context_id: AnalysisContextId
    origin_kind: FactOriginKind
    operation_id: StaticOperationId | None = None
    cfg_edge: tuple[int, int] | None = None
    loop_generation: int | None = None
    property_id: str | None = None


@dataclass(frozen=True)
class FactId:
    """Semantic fact identity; concrete formula structure is intentionally absent."""

    owner: FactOwnerKind
    kind: FactKind
    provenance: FactProvenance
    semantic_key: tuple[str, ...]


FormulaT = TypeVar("FormulaT")


@dataclass(frozen=True)
class Fact(Generic[FormulaT]):
    """An owned formula with stable semantic identity."""

    fact_id: FactId
    formula: FormulaT = field(compare=False, repr=False)


def make_operation_fact(
    operation: object,
    node: object,
    context_id: AnalysisContextId,
    formula: FormulaT,
    *,
    owner: FactOwnerKind,
    kind: FactKind,
    origin_kind: FactOriginKind,
    semantic_role: str,
) -> Fact[FormulaT]:
    """Create an operation-derived fact without inspecting formula structure."""
    operation_id = StaticOperationId.from_operation(operation, node)
    provenance = FactProvenance(
        context_id=context_id,
        origin_kind=origin_kind,
        operation_id=operation_id,
    )
    return Fact(
        fact_id=FactId(
            owner=owner,
            kind=kind,
            provenance=provenance,
            semantic_key=(semantic_role,),
        ),
        formula=formula,
    )


def make_query_fact(
    formula: FormulaT,
    semantic_role: str,
    index: int,
    context_id: AnalysisContextId | None = None,
) -> Fact[FormulaT]:
    """Create a typed query-local assumption without formula-derived identity."""
    context_id = context_id or AnalysisContextId.unbound()
    provenance = FactProvenance(
        context_id=context_id,
        origin_kind=FactOriginKind.QUERY,
    )
    return Fact(
        fact_id=FactId(
            owner=FactOwnerKind.QUERY_LOCAL,
            kind=FactKind.QUERY_ASSUMPTION,
            provenance=provenance,
            semantic_key=(semantic_role, str(index)),
        ),
        formula=formula,
    )


def make_compatibility_query_fact(
    formula: FormulaT,
    semantic_role: str,
    index: int,
    context_id: AnalysisContextId | None = None,
) -> Fact[FormulaT]:
    """Wrap one raw compatibility formula as an ephemeral query-local fact."""
    context_id = context_id or AnalysisContextId.unbound()
    provenance = FactProvenance(
        context_id=context_id,
        origin_kind=FactOriginKind.COMPATIBILITY,
    )
    return Fact(
        fact_id=FactId(
            owner=FactOwnerKind.QUERY_LOCAL,
            kind=FactKind.COMPATIBILITY,
            provenance=provenance,
            semantic_key=(semantic_role, str(index)),
        ),
        formula=formula,
    )


class FactRegistry(Generic[FormulaT]):
    """Deduplicated fact storage keyed only by semantic identity."""

    def __init__(self, facts: tuple[Fact[FormulaT], ...] = ()) -> None:
        self._facts: dict[FactId, Fact[FormulaT]] = {}
        for fact in facts:
            self._facts[fact.fact_id] = fact

    def register(self, fact: Fact[FormulaT]) -> bool:
        """Register a fact, returning True only for the first registration."""
        if fact.fact_id in self._facts:
            return False
        self._facts[fact.fact_id] = fact
        return True

    def get(self, fact_id: FactId) -> Fact[FormulaT] | None:
        """Return a registered fact by semantic identity."""
        return self._facts.get(fact_id)

    def values(self) -> tuple[Fact[FormulaT], ...]:
        """Return registered facts in registration order."""
        return tuple(self._facts.values())

    def ids(self) -> frozenset[FactId]:
        """Return the immutable set of registered identities."""
        return frozenset(self._facts)

    def clear(self) -> None:
        """Remove all registered facts."""
        self._facts.clear()

    def __len__(self) -> int:
        return len(self._facts)


@dataclass(frozen=True, order=True)
class AbstractValueId:
    """Backend-neutral identity of one abstract variable binding."""

    program_name: str
    symbol_name: str
    sort_kind: str
    sort_parameters: tuple[int, ...]
    is_signed: bool
    bit_width: int | None
    minimum: int | None
    maximum: int | None
    is_total: bool
    has_no_overflow: bool
    has_no_underflow: bool
    overflow_operation_id: StaticOperationId | None
    is_unchecked: bool


@dataclass(frozen=True)
class SemanticStateId:
    """Complete semantic identity used for state equality and future caching."""

    reachability: str
    context_id: AnalysisContextId
    abstract_values: tuple[AbstractValueId, ...]
    active_fact_ids: frozenset[FactId]
    storage_summary: tuple[tuple[str, tuple[str, ...], bool], ...]
    comparisons: tuple[
        tuple[
            str,
            StaticOperationId | None,
            tuple[tuple[str, int, int, int, int, bool, bool], ...],
        ],
        ...,
    ]
    dependencies: tuple[tuple[str, tuple[str, ...]], ...]
