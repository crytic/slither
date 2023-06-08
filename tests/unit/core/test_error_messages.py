from pathlib import Path
import pytest


from slither import Slither
from slither.solc_parsing.slither_compilation_unit_solc import InheritanceResolutionError

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
INHERITANCE_ERROR_ROOT = Path(TEST_DATA_DIR, "inheritance_resolution_error")


def test_inheritance_resolution_error(solc_binary_path) -> None:
    with pytest.raises(InheritanceResolutionError):
        solc_path = solc_binary_path("0.8.0")
        Slither(
            Path(INHERITANCE_ERROR_ROOT, "contract_with_duplicate_names.sol").as_posix(),
            solc=solc_path,
        )
