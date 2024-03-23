from pathlib import Path

from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson
from slither import Slither

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data" / "inheritance_resolution"

# https://github.com/crytic/slither/issues/2304
def test_inheritance_with_renaming(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    standard_json = SolcStandardJson()
    for source_file in Path(TEST_DATA_DIR / "renaming").rglob("*.sol"):
        standard_json.add_source_file(Path(source_file).as_posix())
    compilation = CryticCompile(standard_json, solc=solc_path)
    slither = Slither(compilation)

    a = slither.get_contract_from_name("A")[0]
    b = slither.get_contract_from_name("B")[0]
    c = slither.get_contract_from_name("C")[0]

    assert len(a.immediate_inheritance) == 1
    assert a.immediate_inheritance[0] == b
    assert len(a.inheritance) == 2
    assert a.inheritance[0] == b
    assert a.inheritance[1] == c
    assert len(a.explicit_base_constructor_calls) == 1
    a_base_constructor_call = a.explicit_base_constructor_calls[0]
    assert a_base_constructor_call == b.constructor

    assert len(b.inheritance) == 1
    assert b.inheritance[0] == c
    assert len(b.immediate_inheritance) == 1
    assert b.immediate_inheritance[0] == c
    assert len(b.explicit_base_constructor_calls) == 0


def test_inheritance_with_duplicate_names(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    Slither(
        Path(TEST_DATA_DIR / "duplicate_names", "contract_with_duplicate_names.sol").as_posix(),
        solc=solc_path,
    )
