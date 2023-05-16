import os
from pathlib import Path

from slither import Slither
from slither.utils.code_generation import (
    generate_interface,
)

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data" / "code_generation"


def test_interface_generation(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.4")

    sl = Slither(Path(TEST_DATA_DIR, "CodeGeneration.sol").as_posix(), solc=solc_path)

    actual = generate_interface(sl.get_contract_from_name("TestContract")[0])
    expected_path = Path(TEST_DATA_DIR, "TEST_generated_code.sol").as_posix()

    with open(expected_path, "r", encoding="utf-8") as file:
        expected = file.read()

    assert actual == expected

    actual = generate_interface(sl.get_contract_from_name("TestContract")[0], unroll_structs=False)
    expected_path = os.path.join(TEST_DATA_DIR, "TEST_generated_code_not_unrolled.sol")

    with open(expected_path, "r", encoding="utf-8") as file:
        expected = file.read()

    assert actual == expected
