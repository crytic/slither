from pathlib import Path

from slither import Slither
from slither.slithir.operations.new_structure import NewStructure
from slither.slithir.variables.constant import Constant

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
STRUCT_TEST_ROOT = Path(TEST_DATA_DIR, "struct")

def test_struct_constructor(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(Path(STRUCT_TEST_ROOT, "test_constructor.sol").as_posix(), solc=solc_path)

    operations = slither.contracts[0].functions[0].slithir_operations
    constructor_calls = [x for x in operations if isinstance(x, NewStructure)]
    assert len(constructor_calls) == 2

    # Arguments to first call are 2, 3
    assert (
        isinstance(constructor_calls[0].arguments[0], Constant)
        and constructor_calls[0].arguments[0].value == 2
    )
    assert (
        isinstance(constructor_calls[0].arguments[1], Constant)
        and constructor_calls[0].arguments[1].value == 3
    )

    # Arguments to second call are 5, 4 (note the reversed order)
    assert (
        isinstance(constructor_calls[1].arguments[0], Constant)
        and constructor_calls[1].arguments[0].value == 5
    )
    assert (
        isinstance(constructor_calls[1].arguments[1], Constant)
        and constructor_calls[1].arguments[1].value == 4
    )
