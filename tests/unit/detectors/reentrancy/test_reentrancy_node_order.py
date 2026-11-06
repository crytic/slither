from slither.detectors.reentrancy.reentrancy import to_hashable


class OrderedSet(set):
    def __init__(self, values):
        super().__init__(values)
        self.order = values

    def __iter__(self):
        return iter(self.order)


def test_reentrancy_key_orders_equal_node_ids_across_functions(slither_from_solidity_source):
    source = """
    pragma solidity ^0.8.19;
    contract C {
        function f(uint x) external pure returns (uint) { return x + 1; }
        function g(uint x) external pure returns (uint) { return x + 2; }
    }
    """
    with slither_from_solidity_source(source) as slither:
        contract = slither.get_contract_from_name("C")[0]
        nodes = [
            next(n for n in f.nodes if n.node_id == 1)
            for f in contract.functions
            if f.name in ("f", "g")
        ]
        assert len(nodes) == 2
        keys = [
            to_hashable({nodes[0]: OrderedSet(order)}) for order in (nodes, list(reversed(nodes)))
        ]
        assert keys[0] == keys[1]
        assert len({keys[0], keys[1]}) == 1
