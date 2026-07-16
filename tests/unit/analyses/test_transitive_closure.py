"""Tests for transitive closure computation in data dependency analysis."""

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MockContext:
    """Mock context object that mimics function.context structure."""

    context: dict[str, Any] = field(default_factory=dict)


def run_transitive_closure(deps: dict[Any, set[Any]]) -> dict[Any, set[Any]]:
    """Run the worklist algorithm for testing."""
    from slither.analyses.data_dependency.data_dependency import _compute_transitive_closure

    deps = deepcopy(deps)
    _compute_transitive_closure(deps)  # type: ignore[arg-type]  # Test uses strings, prod uses Variables
    return deps


class TestTransitiveClosureCorrectness:
    """Test correctness of transitive closure implementation."""

    def test_empty_graph(self) -> None:
        """Empty graph should remain empty."""
        deps: dict = {}
        result = run_transitive_closure(deps)
        assert result == {}

    def test_single_node_no_deps(self) -> None:
        """Single node with no dependencies."""
        deps = {"A": set()}
        result = run_transitive_closure(deps)
        assert result == {"A": set()}

    def test_single_edge(self) -> None:
        """A -> B, no transitive deps needed."""
        deps = {"A": {"B"}, "B": set()}
        result = run_transitive_closure(deps)
        assert result["A"] == {"B"}
        assert result["B"] == set()

    def test_simple_chain(self) -> None:
        """A -> B -> C should result in A -> {B, C}."""
        deps = {"A": {"B"}, "B": {"C"}, "C": set()}
        result = run_transitive_closure(deps)
        assert result["A"] == {"B", "C"}
        assert result["B"] == {"C"}
        assert result["C"] == set()

    def test_longer_chain(self) -> None:
        """A -> B -> C -> D -> E."""
        deps = {"A": {"B"}, "B": {"C"}, "C": {"D"}, "D": {"E"}, "E": set()}
        expected = {
            "A": {"B", "C", "D", "E"},
            "B": {"C", "D", "E"},
            "C": {"D", "E"},
            "D": {"E"},
            "E": set(),
        }
        result = run_transitive_closure(deps)
        assert result == expected

    def test_diamond(self) -> None:
        """Diamond: A -> B, A -> C, B -> D, C -> D."""
        deps = {"A": {"B", "C"}, "B": {"D"}, "C": {"D"}, "D": set()}
        result = run_transitive_closure(deps)
        assert result["A"] == {"B", "C", "D"}
        assert result["B"] == {"D"}
        assert result["C"] == {"D"}
        assert result["D"] == set()

    def test_cycle_two_nodes(self) -> None:
        """A -> B -> A (cycle)."""
        deps = {"A": {"B"}, "B": {"A"}}
        result = run_transitive_closure(deps)
        # Each should depend on the other but not themselves
        assert result["A"] == {"B"}
        assert result["B"] == {"A"}

    def test_cycle_three_nodes(self) -> None:
        """A -> B -> C -> A (cycle)."""
        deps = {"A": {"B"}, "B": {"C"}, "C": {"A"}}
        result = run_transitive_closure(deps)
        # Each should depend on the other two but not themselves
        assert result["A"] == {"B", "C"}
        assert result["B"] == {"A", "C"}
        assert result["C"] == {"A", "B"}

    def test_self_loop(self) -> None:
        """A -> A (self loop) - algorithm preserves self-loops."""
        deps = {"A": {"A"}}
        result = run_transitive_closure(deps)
        assert result["A"] == {"A"}

    def test_disconnected_components(self) -> None:
        """Two disconnected chains."""
        deps = {"A": {"B"}, "B": set(), "X": {"Y"}, "Y": set()}
        result = run_transitive_closure(deps)
        assert result["A"] == {"B"}
        assert result["B"] == set()
        assert result["X"] == {"Y"}
        assert result["Y"] == set()

    def test_multiple_parents(self) -> None:
        """C depends on A and B independently."""
        deps = {"A": {"X"}, "B": {"Y"}, "C": {"A", "B"}, "X": set(), "Y": set()}
        result = run_transitive_closure(deps)
        assert result["C"] == {"A", "B", "X", "Y"}

    def test_complex_graph(self) -> None:
        """More complex graph with multiple paths."""
        # A -> B -> D
        # A -> C -> D
        # D -> E
        # F -> A (F depends on everything through A)
        deps = {
            "A": {"B", "C"},
            "B": {"D"},
            "C": {"D"},
            "D": {"E"},
            "E": set(),
            "F": {"A"},
        }
        result = run_transitive_closure(deps)
        assert result["A"] == {"B", "C", "D", "E"}
        assert result["B"] == {"D", "E"}
        assert result["C"] == {"D", "E"}
        assert result["D"] == {"E"}
        assert result["E"] == set()
        assert result["F"] == {"A", "B", "C", "D", "E"}

    def test_idempotent(self) -> None:
        """Running twice should give same result."""
        deps = {"A": {"B"}, "B": {"C"}, "C": {"D"}, "D": set()}
        result1 = run_transitive_closure(deps)
        result2 = run_transitive_closure(result1)
        assert result1 == result2

    def test_deps_without_keys(self) -> None:
        """Dependencies that are not themselves keys in the dict."""
        # A depends on B and X, but X is not a key
        deps = {"A": {"B", "X"}, "B": {"C"}, "C": set()}
        result = run_transitive_closure(deps)
        # A should get B's deps (C), but X has no entry so nothing from X
        assert "X" in result["A"]
        assert "B" in result["A"]
        assert "C" in result["A"]

    def test_larger_graph(self) -> None:
        """Larger graph to verify performance characteristics."""
        deps = {
            "N1": {"N2", "N3"},
            "N2": {"N4"},
            "N3": {"N4", "N5"},
            "N4": {"N6"},
            "N5": {"N6"},
            "N6": set(),
            "N7": {"N1", "N8"},
            "N8": {"N9"},
            "N9": set(),
        }
        result = run_transitive_closure(deps)
        # N7 should reach everything through N1
        assert result["N7"] == {"N1", "N2", "N3", "N4", "N5", "N6", "N8", "N9"}
        # N1 should reach N2-N6
        assert result["N1"] == {"N2", "N3", "N4", "N5", "N6"}
