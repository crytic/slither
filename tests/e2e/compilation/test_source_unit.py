from pathlib import Path
import shutil

import pytest
from slither import Slither

# NB: read tests/source_unit/README.md for setup before using this test


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"

foundry_available = shutil.which("forge") is not None
project_ready = Path(TEST_DATA_DIR, "test_source_unit/lib/forge-std").exists()


@pytest.mark.skipif(
    not foundry_available or not project_ready, reason="requires Foundry and project setup"
)
def test_contract_info() -> None:
    slither = Slither(Path(TEST_DATA_DIR, "test_source_unit").as_posix())

    assert len(slither.compilation_units) == 1
    compilation_unit = slither.compilation_units[0]

    for source_unit in compilation_unit.crytic_compile_compilation_unit.source_units.values():
        source_unit.remove_metadata()

    counter_sol = compilation_unit.crytic_compile.filename_lookup(
        Path(TEST_DATA_DIR, "test_source_unit/src/Counter.sol").as_posix()
    )
    assert (
        compilation_unit.scopes[counter_sol].bytecode_init(
            compilation_unit.crytic_compile_compilation_unit, "Counter"
        )
        == "608060405234801561001057600080fd5b5060f78061001f6000396000f3fe6080604052348015600f57600080fd5b5060043610603c5760003560e01c80633fb5c1cb1460415780638381f58a146053578063d09de08a14606d575b600080fd5b6051604c3660046083565b600055565b005b605b60005481565b60405190815260200160405180910390f35b6051600080549080607c83609b565b9190505550565b600060208284031215609457600080fd5b5035919050565b60006001820160ba57634e487b7160e01b600052601160045260246000fd5b506001019056fe"
    )

    counter2_sol = compilation_unit.crytic_compile.filename_lookup(
        "tests/source_unit/src/Counter2.sol"
    )
    assert (
        compilation_unit.scopes[counter2_sol].bytecode_init(
            compilation_unit.crytic_compile_compilation_unit, "Counter"
        )
        == "6080604052348015600f57600080fd5b50603f80601d6000396000f3fe6080604052600080fdfe"
    )
