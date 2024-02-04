from pathlib import Path
from slither import Slither

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"

ALL_TESTS = list(Path(TEST_DATA_DIR).glob("*.vy"))


def pytest_generate_tests(metafunc):
    test_cases = []
    for test_file in ALL_TESTS:
        sl = Slither(test_file.as_posix())
        for contract in sl.contracts:
            if contract.is_interface:
                continue
            for func_or_modifier in contract.functions:
                test_cases.append(
                    (func_or_modifier.canonical_name, func_or_modifier.slithir_cfg_to_dot_str())
                )

    metafunc.parametrize("test_case", test_cases, ids=lambda x: x[0])


def test_vyper_cfgir(test_case, snapshot):
    assert snapshot() == test_case[1]
