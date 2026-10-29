from slither.printers.call import call_graph


def test_renderers_have_stable_order():
    nodes = {f'"node{index}" [label="node{index}"]' for index in range(32)}
    edges = {f'"node{index}" -> "node{index + 1}"' for index in range(32)}
    ordered_body = sorted(nodes) + sorted(edges)
    assert call_graph._render_external_calls(edges).splitlines() == sorted(edges)

    class Contract:
        id = 42
        name = "Contract"

    contract = Contract()
    assert (
        call_graph._render_internal_calls(
            contract, {contract: nodes}, {contract: edges}
        ).splitlines()[2:-1]
        == ordered_body
    )
    assert call_graph._render_solidity_calls(nodes, edges).splitlines()[2:-1] == ordered_body
    assert call_graph._render_toplevel_calls(nodes, edges).splitlines()[2:-1] == ordered_body


def test_contract_clusters_have_stable_order(slither_from_solidity_source):
    source = " ".join(f"contract C{index} {{ function f() external {{}} }}" for index in range(16))
    with slither_from_solidity_source(source) as slither:
        functions = list(slither.compilation_units[0].functions)
        graph = call_graph._process_functions(functions)
        assert graph == call_graph._process_functions(list(reversed(functions)))
        contracts = sorted(slither.contracts, key=lambda contract: contract.id)
        positions = [graph.index(f"subgraph cluster_{contract.id}_") for contract in contracts]
        assert positions == sorted(positions)
