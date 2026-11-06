from itertools import product

from slither.analyses.data_dependency.data_dependency import _compute_transitive_closure


def test_closure_matches_reachability_with_cycles_and_external_leaves():
    # Exhaust all three-vertex directed graphs, including self edges. Each
    # vertex also has a dependency outside the graph, which must propagate.
    vertices = range(3)
    edges = list(product(vertices, repeat=2))
    for mask in range(1 << len(edges)):
        graph = {v: {v + 3} for v in vertices}
        for bit, (source, target) in enumerate(edges):
            if mask & (1 << bit):
                graph[source].add(target)
        expected = {}
        for source in graph:
            visited = set()
            pending = list(graph[source])
            while pending:
                target = pending.pop()
                if target in visited:
                    continue
                visited.add(target)
                pending.extend(graph.get(target, ()))
            if source not in graph[source]:
                visited.discard(source)
            expected[source] = visited
        actual = {v: set(deps) for v, deps in graph.items()}
        _compute_transitive_closure(actual)
        assert actual == expected
        expanded = {v: set(items) for v, items in graph.items()}
        expanded.update({v: set() for v in range(6, 38)})
        _compute_transitive_closure(expanded)
        assert {v: expanded[v] for v in graph} == expected


def test_large_closure_with_external_leaves_and_cycles():
    import random

    rng = random.Random(37)
    for size in [31, 32, 33, 64, 128]:
        for density in [0.01, 0.07, 0.4]:
            original = {
                i: {j for j in range(size + 7) if rng.random() < density} for i in range(size)
            }
            expected = {}
            for key, initial in original.items():
                seen = set(initial)
                queue = list(initial)
                while queue:
                    for target in original.get(queue.pop(), ()):
                        if target not in seen:
                            seen.add(target)
                            queue.append(target)
                if key not in initial:
                    seen.discard(key)
                expected[key] = seen
            actual = {key: set(items) for key, items in original.items()}
            identities = {key: id(items) for key, items in actual.items()}
            _compute_transitive_closure(actual)
            assert actual == expected
            assert identities == {key: id(items) for key, items in actual.items()}


def test_closure_preserves_aliased_sets_and_hash_collisions():
    shared = {2}
    graph = {i: set() for i in range(40)}
    graph[0] = graph[1] = shared
    graph[2] = {3}
    _compute_transitive_closure(graph)
    assert graph[0] is graph[1] is shared
    assert shared == {2, 3}

    class Vertex:
        def __init__(self, index):
            self.index = index

        def __eq__(self, other):
            return isinstance(other, Vertex) and self.index == other.index

        def __hash__(self):
            return 7

    nodes = [Vertex(i) for i in range(40)]
    graph = {node: {nodes[i + 1]} if i < 39 else set() for i, node in enumerate(nodes)}
    _compute_transitive_closure(graph)
    for i, node in enumerate(nodes):
        assert graph[node] == set(nodes[i + 1 :])


def test_closure_preserves_set_subclass_operations():
    operations = []

    class TrackedSet(set):
        def __sub__(self, other):
            operations.append("subtract")
            return super().__sub__(other)

    graph = {i: TrackedSet({i + 1}) if i < 39 else TrackedSet() for i in range(40)}
    _compute_transitive_closure(graph)
    assert operations
    for i, values in graph.items():
        assert values == set(range(i + 1, 40))
        assert type(values) is TrackedSet


def test_closure_preserves_custom_mapping_operations():
    class NoLengthDict(dict):
        def __len__(self):
            raise AssertionError("The original algorithm does not query mapping length")

    graph = NoLengthDict({i: {i + 1} if i < 39 else set() for i in range(40)})
    _compute_transitive_closure(graph)
    for i, values in graph.items():
        assert values == set(range(i + 1, 40))


def test_very_large_sparse_closure_keeps_self_edges():
    # This graph must not require a dense bit matrix to represent its sparse,
    # already closed dependencies. The existing sets remain the same objects.
    graph = {i: {i} for i in range(8193)}
    original = dict(graph)
    _compute_transitive_closure(graph)
    assert all(values == {i} and values is original[i] for i, values in graph.items())
