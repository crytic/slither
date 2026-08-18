"""Unit tests for RoundingDomain copy and join semantics.

RoundingDomain is the only Domain implementation, so these tests pin the
engine-facing contract: Domain.copy() must produce a domain whose tag,
unknown-reason, and trace mappings are independent of the original.

Known limitation (not asserted here): deep_copy shares TraceNode objects
between copies, so in-place mutation of a shared TraceNode is visible to
both. Replacing a trace via set_tag is independent and is covered below.
"""

from __future__ import annotations

from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
    RoundingDomain,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingTag,
    TraceNode,
)
from slither.core.variables.local_variable import LocalVariable


def _variable(name: str) -> LocalVariable:
    variable = LocalVariable()
    variable.name = name
    return variable


def _domain_with(variable: LocalVariable, tag: RoundingTag) -> RoundingDomain:
    domain = RoundingDomain(DomainVariant.STATE)
    domain.state.set_tag(variable, tag)
    return domain


def test_copy_returns_distinct_equal_domain() -> None:
    variable = _variable("x")
    original = _domain_with(variable, RoundingTag.UP)

    copied = original.copy()

    assert copied is not original
    assert copied.state is not original.state
    assert copied.variant == original.variant
    assert copied.state.get_tags(variable) == frozenset({RoundingTag.UP})


def test_retagging_copy_does_not_affect_original() -> None:
    variable = _variable("x")
    original = _domain_with(variable, RoundingTag.UP)

    copied = original.copy()
    copied.state.set_tag(variable, RoundingTag.DOWN)

    assert original.state.get_tags(variable) == frozenset({RoundingTag.UP})
    assert copied.state.get_tags(variable) == frozenset({RoundingTag.DOWN})


def test_new_variable_in_copy_does_not_leak_to_original() -> None:
    seeded = _variable("seeded")
    added = _variable("added")
    original = _domain_with(seeded, RoundingTag.DOWN)

    copied = original.copy()
    copied.state.set_tag(added, RoundingTag.UP)

    assert not original.state.has_tag(added)
    assert copied.state.has_tag(added)


def test_unknown_reason_in_copy_does_not_leak_to_original() -> None:
    variable = _variable("x")
    original = _domain_with(variable, RoundingTag.UP)

    copied = original.copy()
    copied.state.set_tag(
        variable, RoundingTag.UNKNOWN, unknown_reason="conflict in copy"
    )

    assert original.state.get_unknown_reason(variable) is None
    assert copied.state.get_unknown_reason(variable) == "conflict in copy"


def test_trace_replacement_in_copy_does_not_affect_original() -> None:
    variable = _variable("x")
    original_trace = TraceNode(
        function_name="divDown",
        line_number=1,
        tags=frozenset({RoundingTag.DOWN}),
    )
    original = RoundingDomain(DomainVariant.STATE)
    original.state.set_tag(variable, RoundingTag.DOWN, trace=original_trace)

    copied = original.copy()
    replacement = TraceNode(
        function_name="divUp",
        line_number=2,
        tags=frozenset({RoundingTag.UP}),
    )
    copied.state.set_tag(variable, RoundingTag.UP, trace=replacement)

    assert original.state.get_trace(variable) is original_trace
    assert copied.state.get_trace(variable) is replacement


def test_variant_promotion_of_copy_does_not_affect_original() -> None:
    original = RoundingDomain.bottom()

    copied = original.copy()
    variable = _variable("x")
    copied.variant = DomainVariant.STATE
    copied.state.set_tag(variable, RoundingTag.UP)

    assert original.variant == DomainVariant.BOTTOM
    assert not original.state.has_tag(variable)


def test_join_into_copy_does_not_affect_original() -> None:
    variable = _variable("x")
    original = _domain_with(variable, RoundingTag.UP)
    other = _domain_with(variable, RoundingTag.DOWN)

    copied = original.copy()
    changed = copied.join(other)

    assert changed
    assert copied.state.get_tags(variable) == frozenset(
        {RoundingTag.UP, RoundingTag.DOWN}
    )
    assert original.state.get_tags(variable) == frozenset({RoundingTag.UP})


def test_join_from_bottom_copies_rather_than_aliases() -> None:
    variable = _variable("x")
    source = _domain_with(variable, RoundingTag.UP)

    target = RoundingDomain.bottom()
    target.join(source)
    target.state.set_tag(variable, RoundingTag.DOWN)

    assert source.state.get_tags(variable) == frozenset({RoundingTag.UP})


def test_copy_shares_trace_node_objects() -> None:
    """Pin current behavior: copies share TraceNode objects.

    deep_copy() copies the trace *mapping* but not the TraceNode values,
    so in-place mutation of a trace reached through a copy is visible in
    the original. No live code path mutates a trace after copying today,
    making this latent. This test documents the sharing — it does NOT
    assert it is desirable. If the interprocedural refactor deep-copies
    traces (or makes TraceNode immutable), update this test deliberately
    rather than treating the failure as a regression.
    """
    variable = _variable("x")
    trace = TraceNode(
        function_name="divDown",
        line_number=1,
        tags=frozenset({RoundingTag.DOWN}),
    )
    original = RoundingDomain(DomainVariant.STATE)
    original.state.set_tag(variable, RoundingTag.DOWN, trace=trace)

    copied = original.copy()
    copied_trace = copied.state.get_trace(variable)
    assert copied_trace is trace, "copy is expected to share the TraceNode"

    copied_trace.branch_condition = "mutated via copy"
    assert original.state.get_trace(variable).branch_condition == (
        "mutated via copy"
    )
