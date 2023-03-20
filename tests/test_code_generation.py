import os

from solc_select import solc_select

from slither import Slither
from slither.utils.code_generation import (
    generate_interface,
)

SLITHER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_TEST_ROOT = os.path.join(SLITHER_ROOT, "tests", "code_generation")


def test_interface_generation() -> None:
    solc_select.switch_global_version("0.8.4", always_install=True)

    sl = Slither(os.path.join(CODE_TEST_ROOT, "CodeGeneration.sol"))

    actual = generate_interface(sl.get_contract_from_name("TestContract")[0])
    expected_path = os.path.join(CODE_TEST_ROOT, "TEST_generated_code.sol")

    with open(expected_path, "r", encoding="utf-8") as file:
        expected = file.read()

    assert actual == expected
