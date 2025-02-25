from pathlib import Path
from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson

from slither import Slither

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
SCOPE_RENAMING_TEST_DATA_DIR = Path(TEST_DATA_DIR, "scope_with_renaming")

# https://github.com/crytic/slither/issues/2454
def test_find_variable_scope_with_renaming(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.24")
    standard_json = SolcStandardJson()
    for source_file in SCOPE_RENAMING_TEST_DATA_DIR.rglob("**/*.sol"):
        standard_json.add_source_file(Path(source_file).as_posix())
    compilation = CryticCompile(standard_json, solc=solc_path)
    Slither(compilation, disallow_partial=True)
