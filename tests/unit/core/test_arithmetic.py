from pathlib import Path

from slither import Slither
from slither.utils.arithmetic import unchecked_arithemtic_usage
from slither.slithir.operations import Binary, Unary, Assignment
from slither.slithir.variables.temporary import TemporaryVariable

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data" / "arithmetic_usage"


def test_arithmetic_usage(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(Path(TEST_DATA_DIR, "test.sol").as_posix(), solc=solc_path)

    assert {
        f.source_mapping.content_hash for f in unchecked_arithemtic_usage(slither.contracts[0])
    } == {"2b4bc73cf59d486dd9043e840b5028b679354dd9", "e4ecd4d0fda7e762d29aceb8425f2c5d4d0bf962"}


def test_scope_is_checked(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(Path(TEST_DATA_DIR, "unchecked_scope.sol").as_posix(), solc=solc_path)
    func = slither.get_contract_from_name("TestScope")[0].get_function_from_full_name(
        "scope(uint256)"
    )
    bin_op_is_checked = {}
    for node in func.nodes:
        for op in node.irs:
            if isinstance(op, (Binary, Unary)):
                bin_op_is_checked[op.lvalue] = op.node.scope.is_checked
            if isinstance(op, Assignment) and isinstance(op.rvalue, TemporaryVariable):
                if op.lvalue.name.startswith("checked"):
                    assert bin_op_is_checked[op.rvalue] is True
                else:
                    assert bin_op_is_checked[op.rvalue] is False
