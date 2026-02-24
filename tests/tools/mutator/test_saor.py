import tempfile
from pathlib import Path

from slither import Slither
from slither.tools.mutator.mutators.SAOR import SAOR

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def test_saor_generates_patches(solc_binary_path):
    """SAOR should generate swap patches for same-typed arguments."""
    solc_path = solc_binary_path("0.8.15")
    file_path = (TEST_DATA_DIR / "saor" / "saor.sol").as_posix()
    sl = Slither(file_path, solc=solc_path, compile_force_framework="solc")

    contract = next(c for c in sl.contracts if c.name == "SAORTest")

    with tempfile.TemporaryDirectory() as tmpdir:
        mutator = SAOR(
            sl.compilation_units[0],
            timeout=30,
            testing_command="true",
            testing_directory=None,
            contract_instance=contract,
            solc_remappings=None,
            verbose=False,
            output_folder=Path(tmpdir),
            dont_mutate_line=[],
            target_selectors=None,
            target_modifiers=None,
        )

        result = mutator._mutate()

        # Should generate patches (at least for add(1,2) and transfer(addr,addr,uint))
        assert "patches" in result, "SAOR should generate at least one patch"
        file_patches = result["patches"]

        # Verify patches contain the test file
        assert file_path in file_patches, f"Expected patches for {file_path}"

        # Each patch should have the required fields
        for patch in file_patches[file_path]:
            assert "start" in patch
            assert "end" in patch
            assert "old_string" in patch
            assert "new_string" in patch
            assert patch["old_string"] != patch["new_string"]
