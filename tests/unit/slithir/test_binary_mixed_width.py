from slither.core.solidity_types import ElementaryType
from slither.slithir.operations import Binary, LibraryCall

CONTRACT = """
pragma solidity ^0.8.0;

library Lib {
    function cast(uint256 x) internal pure returns (uint128) {
        return uint128(x);
    }
}

contract C {
    using Lib for uint256;

    function leftNarrow(uint128 a, uint256 d) internal pure returns (uint128) {
        return (a + d).cast();
    }

    function rightNarrow(uint128 a, uint256 d) internal pure returns (uint128) {
        return (d + a).cast();
    }
}
"""


def test_binary_result_type_widens_to_wider_operand(slither_from_solidity_source) -> None:
    with slither_from_solidity_source(CONTRACT) as slither:
        contract = slither.get_contract_from_name("C")[0]
        function = contract.get_function_from_signature("leftNarrow(uint128,uint256)")

        binary_ops = [ir for ir in function.slithir_operations if isinstance(ir, Binary)]
        assert len(binary_ops) == 1
        # The narrower left operand (uint128) must not truncate the result type:
        # Solidity widens the sum to uint256, and so must Slither.
        assert binary_ops[0].lvalue.type == ElementaryType("uint256")


def test_using_for_resolves_on_mixed_width_sum(slither_from_solidity_source) -> None:
    with slither_from_solidity_source(CONTRACT) as slither:
        contract = slither.get_contract_from_name("C")[0]

        for sig in ("leftNarrow(uint128,uint256)", "rightNarrow(uint128,uint256)"):
            function = contract.get_function_from_signature(sig)
            library_calls = [
                ir for ir in function.slithir_operations if isinstance(ir, LibraryCall)
            ]
            assert len(library_calls) == 1
            assert library_calls[0].function is not None
            assert library_calls[0].function.name == "cast"
