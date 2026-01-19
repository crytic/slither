"""Tests for transitive_close_dependencies function optimization."""

from copy import deepcopy
from dataclasses import dataclass, field


@dataclass
class MockContext:
    """Mock context object that mimics function.context structure."""

    context: dict = field(default_factory=dict)


def run_transitive_closure_legacy(deps: dict) -> dict:
    """Run the original algorithm for comparison."""
    from collections import defaultdict

    # Make a deep copy to avoid mutation
    deps = deepcopy(deps)
    changed = True
    keys = deps.keys()
    while changed:
        changed = False
        to_add = defaultdict(set)
        for key, items in deps.items():
            for item in items & keys:
                to_add[key].update(deps[item] - {key} - items)
        for k, v in to_add.items():
            if v:
                changed = True
                deps[k] |= v
    return deps


def run_transitive_closure_warshall(deps: dict) -> dict:
    """Warshall's algorithm - O(n^3) but cache-friendly."""
    deps = deepcopy(deps)
    keys = list(deps.keys())
    for k in keys:
        k_deps = deps.get(k, set())
        for i in keys:
            if k in deps.get(i, set()):
                # i depends on k, so i also depends on everything k depends on
                deps[i] |= k_deps - {i}
    return deps


def run_transitive_closure_dfs(deps: dict) -> dict:
    """DFS-based reachability - O(V*(V+E)), good for sparse graphs."""
    deps = deepcopy(deps)
    keys = list(deps.keys())

    def dfs(node: object, visited: set) -> set:
        for neighbor in deps.get(node, set()) - visited:
            visited.add(neighbor)
            dfs(neighbor, visited)
        return visited

    for key in keys:
        deps[key] = dfs(key, set()) - {key}
    return deps


def run_transitive_closure_worklist(deps: dict) -> dict:
    """Worklist algorithm - only reprocess changed nodes."""
    deps = deepcopy(deps)
    # Build reverse index: for each node, who depends on it?
    reverse_deps: dict[object, set] = {}
    for key, items in deps.items():
        for item in items:
            if item not in reverse_deps:
                reverse_deps[item] = set()
            reverse_deps[item].add(key)

    # Process nodes whose dependencies we need to propagate
    worklist = set(deps.keys())
    while worklist:
        node = worklist.pop()
        node_deps = deps.get(node, set())
        # For everyone who depends on this node
        for dependent in reverse_deps.get(node, set()):
            # Add node's dependencies to their dependencies
            new_deps = node_deps - deps[dependent] - {dependent}
            if new_deps:
                deps[dependent] |= new_deps
                # Update reverse index for new deps
                for new_dep in new_deps:
                    if new_dep not in reverse_deps:
                        reverse_deps[new_dep] = set()
                    reverse_deps[new_dep].add(dependent)
                worklist.add(dependent)
    return deps


# All implementations to test
IMPLEMENTATIONS = [
    ("legacy", run_transitive_closure_legacy),
    ("warshall", run_transitive_closure_warshall),
    ("dfs", run_transitive_closure_dfs),
    ("worklist", run_transitive_closure_worklist),
]


class TestTransitiveClosureCorrectness:
    """Test correctness of transitive closure implementations."""

    def test_empty_graph(self) -> None:
        """Empty graph should remain empty."""
        deps: dict = {}
        for name, impl in IMPLEMENTATIONS:
            result = impl(deps)
            assert result == {}, f"{name} failed on empty graph"

    def test_single_node_no_deps(self) -> None:
        """Single node with no dependencies."""
        deps = {"A": set()}
        for name, impl in IMPLEMENTATIONS:
            result = impl(deps)
            assert result == {"A": set()}, f"{name} failed on single node"

    def test_single_edge(self) -> None:
        """A -> B, no transitive deps needed."""
        deps = {"A": {"B"}, "B": set()}
        for name, impl in IMPLEMENTATIONS:
            result = impl(deps)
            assert result["A"] == {"B"}, f"{name} failed on single edge"
            assert result["B"] == set(), f"{name} failed on single edge"

    def test_simple_chain(self) -> None:
        """A -> B -> C should result in A -> {B, C}."""
        deps = {"A": {"B"}, "B": {"C"}, "C": set()}
        for name, impl in IMPLEMENTATIONS:
            result = impl(deps)
            assert result["A"] == {"B", "C"}, f"{name} failed on chain: {result}"
            assert result["B"] == {"C"}, f"{name} failed on chain: {result}"
            assert result["C"] == set(), f"{name} failed on chain: {result}"

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
        for name, impl in IMPLEMENTATIONS:
            result = impl(deps)
            assert result == expected, f"{name} failed on longer chain: {result}"

    def test_diamond(self) -> None:
        """Diamond: A -> B, A -> C, B -> D, C -> D."""
        deps = {"A": {"B", "C"}, "B": {"D"}, "C": {"D"}, "D": set()}
        for name, impl in IMPLEMENTATIONS:
            result = impl(deps)
            assert result["A"] == {"B", "C", "D"}, f"{name} failed on diamond: {result}"
            assert result["B"] == {"D"}, f"{name} failed on diamond: {result}"
            assert result["C"] == {"D"}, f"{name} failed on diamond: {result}"
            assert result["D"] == set(), f"{name} failed on diamond: {result}"

    def test_cycle_two_nodes(self) -> None:
        """A -> B -> A (cycle)."""
        deps = {"A": {"B"}, "B": {"A"}}
        for name, impl in IMPLEMENTATIONS:
            result = impl(deps)
            # Each should depend on the other but not themselves
            assert result["A"] == {"B"}, f"{name} failed on cycle: {result}"
            assert result["B"] == {"A"}, f"{name} failed on cycle: {result}"

    def test_cycle_three_nodes(self) -> None:
        """A -> B -> C -> A (cycle)."""
        deps = {"A": {"B"}, "B": {"C"}, "C": {"A"}}
        for name, impl in IMPLEMENTATIONS:
            result = impl(deps)
            # Each should depend on the other two but not themselves
            assert result["A"] == {"B", "C"}, f"{name} failed on 3-cycle: {result}"
            assert result["B"] == {"A", "C"}, f"{name} failed on 3-cycle: {result}"
            assert result["C"] == {"A", "B"}, f"{name} failed on 3-cycle: {result}"

    def test_self_loop(self) -> None:
        """A -> A (self loop) - verify consistent handling."""
        deps = {"A": {"A"}}
        # Legacy preserves self-loops; DFS removes self (by design: `- {key}`)
        # This is an edge case - normal data deps don't have self-loops
        legacy_result = run_transitive_closure_legacy(deepcopy(deps))
        for name, impl in IMPLEMENTATIONS:
            result = impl(deps)
            if name == "dfs":
                # DFS explicitly removes self-references
                assert result["A"] == set(), f"dfs should remove self: {result}"
            else:
                assert result == legacy_result, f"{name} differs from legacy: {result}"

    def test_disconnected_components(self) -> None:
        """Two disconnected chains."""
        deps = {"A": {"B"}, "B": set(), "X": {"Y"}, "Y": set()}
        for name, impl in IMPLEMENTATIONS:
            result = impl(deps)
            assert result["A"] == {"B"}, f"{name} failed on disconnected: {result}"
            assert result["B"] == set(), f"{name} failed on disconnected: {result}"
            assert result["X"] == {"Y"}, f"{name} failed on disconnected: {result}"
            assert result["Y"] == set(), f"{name} failed on disconnected: {result}"

    def test_multiple_parents(self) -> None:
        """C depends on A and B independently."""
        deps = {"A": {"X"}, "B": {"Y"}, "C": {"A", "B"}, "X": set(), "Y": set()}
        for name, impl in IMPLEMENTATIONS:
            result = impl(deps)
            assert result["C"] == {"A", "B", "X", "Y"}, f"{name} failed: {result}"

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
        for name, impl in IMPLEMENTATIONS:
            result = impl(deps)
            assert result["A"] == {"B", "C", "D", "E"}, f"{name} A: {result}"
            assert result["B"] == {"D", "E"}, f"{name} B: {result}"
            assert result["C"] == {"D", "E"}, f"{name} C: {result}"
            assert result["D"] == {"E"}, f"{name} D: {result}"
            assert result["E"] == set(), f"{name} E: {result}"
            assert result["F"] == {"A", "B", "C", "D", "E"}, f"{name} F: {result}"

    def test_idempotent(self) -> None:
        """Running twice should give same result."""
        deps = {"A": {"B"}, "B": {"C"}, "C": {"D"}, "D": set()}
        for name, impl in IMPLEMENTATIONS:
            result1 = impl(deps)
            result2 = impl(result1)
            assert result1 == result2, f"{name} not idempotent"

    def test_deps_without_keys(self) -> None:
        """Dependencies that are not themselves keys in the dict."""
        # A depends on B and X, but X is not a key
        deps = {"A": {"B", "X"}, "B": {"C"}, "C": set()}
        for name, impl in IMPLEMENTATIONS:
            result = impl(deps)
            # A should get B's deps (C), but X has no entry so nothing from X
            assert "X" in result["A"], f"{name} should keep X: {result}"
            assert "B" in result["A"], f"{name} should keep B: {result}"
            assert "C" in result["A"], f"{name} should add C from B: {result}"


class TestImplementationsMatch:
    """Verify all implementations produce identical results."""

    def test_all_match_on_various_graphs(self) -> None:
        """All implementations should match legacy on various inputs."""
        test_cases = [
            {},
            {"A": set()},
            {"A": {"B"}, "B": set()},
            {"A": {"B"}, "B": {"C"}, "C": set()},
            {"A": {"B", "C"}, "B": {"D"}, "C": {"D"}, "D": set()},
            {"A": {"B"}, "B": {"A"}},
            {"A": {"B"}, "B": {"C"}, "C": {"A"}},
            {"A": {"B"}, "B": set(), "X": {"Y"}, "Y": set()},
            {
                "A": {"B", "C"},
                "B": {"D"},
                "C": {"D"},
                "D": {"E"},
                "E": set(),
                "F": {"A"},
            },
            # Large-ish random-like graph
            {
                "N1": {"N2", "N3"},
                "N2": {"N4"},
                "N3": {"N4", "N5"},
                "N4": {"N6"},
                "N5": {"N6"},
                "N6": set(),
                "N7": {"N1", "N8"},
                "N8": {"N9"},
                "N9": set(),
            },
        ]
        for deps in test_cases:
            baseline = run_transitive_closure_legacy(deps)
            for name, impl in IMPLEMENTATIONS:
                if name == "legacy":
                    continue
                result = impl(deps)
                assert result == baseline, f"{name} differs from legacy on {deps}"


class TestActualImplementations:
    """Test the actual implementations in the module."""

    def test_module_implementations_match(self) -> None:
        """Verify module implementations match expected behavior."""
        from slither.analyses.data_dependency.data_dependency import (
            _transitive_close_legacy,
            _transitive_close_warshall,
            _transitive_close_dfs,
            _transitive_close_worklist,
        )

        test_cases = [
            {"A": {"B"}, "B": {"C"}, "C": set()},
            {"A": {"B", "C"}, "B": {"D"}, "C": {"D"}, "D": set()},
            {"A": {"B"}, "B": {"A"}},
        ]

        for deps in test_cases:
            # Get legacy baseline
            legacy_deps = deepcopy(deps)
            _transitive_close_legacy(legacy_deps)

            for impl in [
                _transitive_close_warshall,
                _transitive_close_dfs,
                _transitive_close_worklist,
            ]:
                test_deps = deepcopy(deps)
                impl(test_deps)
                assert test_deps == legacy_deps, f"{impl.__name__} differs on {deps}"
