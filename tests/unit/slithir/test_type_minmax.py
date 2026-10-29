from pathlib import Path

from slither import Slither
from slither.slithir.operations import Assignment
from slither.slithir.variables import Constant

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def _folded_constant(func):
    """Return the value of the first `TMP := <constant>` assignment in `func`."""
    for op in func.slithir_operations:
        if isinstance(op, Assignment) and isinstance(op.rvalue, Constant):
            return op.rvalue.value
    return None


def test_type_minmax_parenthesized(solc_binary_path) -> None:
    # Regression test for `(type(X)).max` / `.min`: the redundant parentheses
    # must be unwrapped so the value folds to a constant, exactly like the
    # non-parenthesized `type(X).max`. Before the fix, building the Slither
    # object raised "type(uint8).max is unknown" during IR generation.
    solc_path = solc_binary_path("0.8.19")
    slither = Slither(
        Path(TEST_DATA_DIR, "type_minmax_parenthesized.sol").as_posix(), solc=solc_path
    )
    contract = slither.get_contract_from_name("C")[0]

    expected = {
        "paren_max()": 255,
        "paren_min()": 0,
        "nested_paren_max()": 2**256 - 1,
        "signed_min()": -(2**255),
        "plain_max()": 255,
    }
    for signature, value in expected.items():
        func = contract.get_function_from_full_name(signature)
        assert _folded_constant(func) == value, signature
