from pathlib import Path
from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson

from slither import Slither

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
IMPORTED_STRUCT_TEST_DATA_DIR = Path(TEST_DATA_DIR, "imported_struct_in_library")


# https://github.com/crytic/slither/issues/2954
def test_imported_struct_from_library(solc_binary_path) -> None:
    """Test that structs defined in an imported library are resolved correctly."""
    solc_path = solc_binary_path("0.8.0")
    standard_json = SolcStandardJson()
    for source_file in IMPORTED_STRUCT_TEST_DATA_DIR.rglob("**/*.sol"):
        standard_json.add_source_file(Path(source_file).as_posix())
    compilation = CryticCompile(standard_json, solc=solc_path)
    sl = Slither(compilation, disallow_partial=True)

    # Verify the struct types were resolved correctly
    consumer = next(c for c in sl.contracts if c.name == "Consumer")
    changes_var = next(v for v in consumer.state_variables if v.name == "currentChanges")
    assert "ShiftChanges" in str(changes_var.type)
