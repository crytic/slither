from pathlib import Path
from solc_select import solc_select

from slither import Slither
from slither.core.declarations.function import FunctionType

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def test_fallback_receive():
    solc_select.switch_global_version("0.6.12", always_install=True)
    file = Path(TEST_DATA_DIR, "fallback.sol").as_posix()
    slither = Slither(file)
    fake_fallback = slither.get_contract_from_name("FakeFallback")[0]
    real_fallback = slither.get_contract_from_name("Fallback")[0]

    assert fake_fallback.fallback_function is None
    assert fake_fallback.receive_function is None
    assert real_fallback.fallback_function.function_type == FunctionType.FALLBACK
    assert real_fallback.receive_function.function_type == FunctionType.RECEIVE
