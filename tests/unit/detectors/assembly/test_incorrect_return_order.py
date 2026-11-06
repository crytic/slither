from slither.core.declarations import SolidityFunction
from slither.detectors.assembly.incorrect_return import IncorrectReturn

SOURCE = """
pragma solidity ^0.8.19;
contract C {
    function halt(bool x) internal {
        if (x) {
            assembly { return(0, 0) }
        }
        assembly { return(0, 32) }
    }

    function bad() external returns (bool) {
        halt(true);
        return true;
    }
}
"""


def test_incorrect_return_witness_does_not_depend_on_call_order(slither_from_solidity_source):
    with slither_from_solidity_source(SOURCE) as slither:
        halt = slither.get_contract_from_name("C")[0].get_function_from_signature("halt(bool)")
        calls = halt.all_solidity_calls()
        returns = [ir for ir in calls if ir.function == SolidityFunction("return(uint256,uint256)")]
        assert len(returns) == 2
        slither.register_detector(IncorrectReturn)
        outputs = []
        # all_solidity_calls() is deduplicated through a set, so its order follows
        # identity hashes. Check that either order reports the same witness.
        for order in (calls, list(reversed(calls))):
            halt._all_solidity_calls = order
            slither._currently_seen_resuts.clear()
            outputs.append(slither.run_detectors()[0])
        assert outputs[0] == outputs[1]
        assert len(outputs[0]) == 1
        witness = outputs[0][0]["elements"][2]
        assert witness["type"] == "node"
        assert witness["source_mapping"]["lines"] == [6]
