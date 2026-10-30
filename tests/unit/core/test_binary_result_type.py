import pytest

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations import Binary


@pytest.mark.parametrize(
    ("signature", "result"),
    [
        ("addL(uint128,uint256)", "uint256"),  # arithmetic widens to the wider operand
        ("andL(uint128,uint256)", "uint256"),  # bitwise widens too
        ("shlL(uint128,uint256)", "uint128"),  # shift result follows the left operand
        ("shrL(uint128,uint256)", "uint128"),
        ("powL(uint256,uint8)", "uint256"),  # exponentiation result follows the base
    ],
)
def test_binary_result_type_matches_solc(slither_from_solidity_source, signature, result):
    src = """
    pragma solidity ^0.8.0;
    contract C {
        function addL(uint128 a, uint256 d) internal pure returns (uint256) { return a + d; }
        function andL(uint128 a, uint256 d) internal pure returns (uint256) { return a & d; }
        function shlL(uint128 a, uint256 d) internal pure returns (uint128) { return a << d; }
        function shrL(uint128 a, uint256 d) internal pure returns (uint128) { return a >> d; }
        function powL(uint256 a, uint8 d) internal pure returns (uint256) { return a ** d; }
    }
    """
    with slither_from_solidity_source(src) as slither:
        fn = slither.get_contract_from_name("C")[0].get_function_from_signature(signature)
        binary = next(ir for ir in fn.slithir_operations if isinstance(ir, Binary))
        assert binary.lvalue.type == ElementaryType(result)
