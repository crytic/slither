from slither import Slither
from slither.visitors.expression.constants_folding import ConstantFolding


def test_constant_folding_unary():
    Slither("./tests/constant_folding_unary.sol")

def test_constant_folding_rational():
    s = Slither("./tests/constant_folding_rational.sol")
    contract = s.get_contract_from_name("C")[0]

    variable_a = contract.get_state_variable_from_name("a")
    assert str(variable_a.type) == "uint256"
    assert str(ConstantFolding(variable_a.expression, "uint256").result()) == "10"

    variable_b = contract.get_state_variable_from_name("b")
    assert str(variable_b.type) == "int128"
    assert str(ConstantFolding(variable_b.expression, "int128").result()) == "2"

    variable_c = contract.get_state_variable_from_name("c")
    assert str(variable_c.type) == "int64"
    assert str(ConstantFolding(variable_c.expression, "int64").result()) == "3"

    variable_d = contract.get_state_variable_from_name("d")
    assert str(variable_d.type) == "int256"
    assert str(ConstantFolding(variable_d.expression, "int256").result()) == "1500"

    variable_e = contract.get_state_variable_from_name("e")
    assert str(variable_e.type) == "uint256"
    assert str(ConstantFolding(variable_e.expression, "uint256").result()) == "57896044618658097711785492504343953926634992332820282019728792003956564819968"