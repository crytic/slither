from slither import Slither


def test_constant_folding_unary():
    Slither("./tests/constant_folding_unary.sol")
