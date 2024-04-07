from pathlib import Path
from slither import Slither
from slither.core.declarations.contract import Contract
from slither.slithir.operations import LibraryCall, InternalCall

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def test_top_level_using_for(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.24")
    slither = Slither(Path(TEST_DATA_DIR, "top_level_using_for.sol").as_posix(), solc=solc_path)

    function = slither.compilation_units[0].functions_top_level[1]
    assert function.name == "b"

    # LIBRARY_CALL, dest:Lib, function:Lib.a(uint256), arguments:['4']
    first_ir = function.slithir_operations[0]
    assert (
        isinstance(first_ir, LibraryCall)
        and isinstance(first_ir.destination, Contract)
        and first_ir.destination.name == "Lib"
        and first_ir.function_name == "a"
        and len(first_ir.arguments) == 1
    )

    # INTERNAL_CALL, c(uint256)(y)
    second_ir = function.slithir_operations[1]
    assert (
        isinstance(second_ir, InternalCall)
        and second_ir.function_name == "c"
        and len(second_ir.arguments) == 1
        and second_ir.arguments[0].name == "y"
    )

    # LIBRARY_CALL, dest:Lib, function:Lib.a(uint256), arguments:['y']
    third_ir = function.slithir_operations[2]
    assert (
        isinstance(third_ir, LibraryCall)
        and isinstance(third_ir.destination, Contract)
        and third_ir.destination.name == "Lib"
        and third_ir.function_name == "a"
        and len(third_ir.arguments) == 1
        and third_ir.arguments[0].name == "y"
    )
