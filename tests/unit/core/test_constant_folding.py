from pathlib import Path
from slither import Slither
from slither.visitors.expression.constants_folding import ConstantFolding

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
CONSTANT_FOLDING_TEST_ROOT = Path(TEST_DATA_DIR, "constant_folding")


def test_constant_folding_unary(solc_binary_path):
    solc_path = solc_binary_path("0.8.0")
    file = Path(CONSTANT_FOLDING_TEST_ROOT, "constant_folding_unary.sol").as_posix()
    Slither(file, solc=solc_path)


def test_constant_folding_rational(solc_binary_path):
    solc_path = solc_binary_path("0.8.0")
    s = Slither(
        Path(CONSTANT_FOLDING_TEST_ROOT, "constant_folding_rational.sol").as_posix(), solc=solc_path
    )
    contract = s.get_contract_from_name("C")[0]

    variable_a = contract.get_state_variable_from_name("a")
    assert str(variable_a.type) == "uint256"
    assert ConstantFolding(variable_a.expression, "uint256").result().value == 10

    variable_b = contract.get_state_variable_from_name("b")
    assert str(variable_b.type) == "int128"
    assert ConstantFolding(variable_b.expression, "int128").result().value == 2

    variable_c = contract.get_state_variable_from_name("c")
    assert str(variable_c.type) == "int64"
    assert ConstantFolding(variable_c.expression, "int64").result().value == 3

    variable_d = contract.get_state_variable_from_name("d")
    assert str(variable_d.type) == "int256"
    assert ConstantFolding(variable_d.expression, "int256").result().value == 1500

    variable_e = contract.get_state_variable_from_name("e")
    assert str(variable_e.type) == "uint256"
    assert (
        ConstantFolding(variable_e.expression, "uint256").result().value
        == 57896044618658097711785492504343953926634992332820282019728792003956564819968
    )

    variable_f = contract.get_state_variable_from_name("f")
    assert str(variable_f.type) == "uint256"
    assert (
        ConstantFolding(variable_f.expression, "uint256").result().value
        == 115792089237316195423570985008687907853269984665640564039457584007913129639935
    )

    variable_g = contract.get_state_variable_from_name("g")
    assert str(variable_g.type) == "int64"
    assert ConstantFolding(variable_g.expression, "int64").result().value == -7


# pylint: disable=too-many-locals
def test_constant_folding_binary_expressions(solc_binary_path):
    sl = Slither(
        Path(CONSTANT_FOLDING_TEST_ROOT, "constant_folding_binop.sol").as_posix(),
        solc=solc_binary_path("0.8.0"),
    )
    contract = sl.get_contract_from_name("BinOp")[0]

    variable_a = contract.get_state_variable_from_name("a")
    assert str(variable_a.type) == "uint256"
    assert ConstantFolding(variable_a.expression, "uint256").result().value == 0

    variable_b = contract.get_state_variable_from_name("b")
    assert str(variable_b.type) == "uint256"
    assert ConstantFolding(variable_b.expression, "uint256").result().value == 3

    variable_c = contract.get_state_variable_from_name("c")
    assert str(variable_c.type) == "uint256"
    assert ConstantFolding(variable_c.expression, "uint256").result().value == 3

    variable_d = contract.get_state_variable_from_name("d")
    assert str(variable_d.type) == "bool"
    assert ConstantFolding(variable_d.expression, "bool").result().value is False

    variable_e = contract.get_state_variable_from_name("e")
    assert str(variable_e.type) == "bool"
    assert ConstantFolding(variable_e.expression, "bool").result().value is False

    variable_f = contract.get_state_variable_from_name("f")
    assert str(variable_f.type) == "bool"
    assert ConstantFolding(variable_f.expression, "bool").result().value is True

    variable_g = contract.get_state_variable_from_name("g")
    assert str(variable_g.type) == "bool"
    assert ConstantFolding(variable_g.expression, "bool").result().value is False

    variable_h = contract.get_state_variable_from_name("h")
    assert str(variable_h.type) == "bool"
    assert ConstantFolding(variable_h.expression, "bool").result().value is False

    variable_i = contract.get_state_variable_from_name("i")
    assert str(variable_i.type) == "bool"
    assert ConstantFolding(variable_i.expression, "bool").result().value is True

    variable_j = contract.get_state_variable_from_name("j")
    assert str(variable_j.type) == "bool"
    assert ConstantFolding(variable_j.expression, "bool").result().value is False

    variable_k = contract.get_state_variable_from_name("k")
    assert str(variable_k.type) == "bool"
    assert ConstantFolding(variable_k.expression, "bool").result().value is True

    variable_l = contract.get_state_variable_from_name("l")
    assert str(variable_l.type) == "uint256"
    assert (
        ConstantFolding(variable_l.expression, "uint256").result().value
        == 115792089237316195423570985008687907853269984665640564039457584007913129639935
    )

    IMPLEMENTATION_SLOT = contract.get_state_variable_from_name("IMPLEMENTATION_SLOT")
    assert str(IMPLEMENTATION_SLOT.type) == "bytes32"
    assert (
        int.from_bytes(
            ConstantFolding(IMPLEMENTATION_SLOT.expression, "bytes32").result().value,
            byteorder="big",
        )
        == 24440054405305269366569402256811496959409073762505157381672968839269610695612
    )

    variable_m = contract.get_state_variable_from_name("m")
    assert str(variable_m.type) == "bytes2"
    assert ConstantFolding(variable_m.expression, "bytes2").result().value == "ab"
