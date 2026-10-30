from pathlib import Path
from slither import Slither

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def test_function_id_rec_structure(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "type_helpers.sol").as_posix(), solc=solc_path)
    for compilation_unit in slither.compilation_units:
        for function in compilation_unit.functions:
            assert function.solidity_signature


def test_recursive_struct_signature_stable(solc_binary_path) -> None:
    # An internal-only recursive structure must still terminate and keep its
    # upstream canonical rendering. type_helpers.sol defines St{St[] a; uint b;}.
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "type_helpers.sol").as_posix(), solc=solc_path)
    function = next(fn for cu in slither.compilation_units for fn in cu.functions if fn.name == "f")
    assert function.solidity_signature == "f((A.St[],uint256))"


# A shared mutable `seen` set used to leak across sibling structure fields, so
# only the first field whose type required conversion was converted (issue
# #3064). The expected signatures are the compiler canonical forms, verified
# with `solc --hashes`; they also exercise a repeated non-recursive structure.
REPEATED_FIELD_SIGNATURES = {
    "fAlias": "fAlias((uint256,uint256))",
    "fEnum": "fEnum((uint8,uint8))",
    "fContract": "fContract((address,address))",
    "fRepeatedStruct": "fRepeatedStruct(((uint256,address),(uint256,address)))",
}


def test_solidity_signature_repeated_convertible_fields(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.24")
    slither = Slither(
        Path(TEST_DATA_DIR, "signature_repeated_fields.sol").as_posix(), solc=solc_path
    )
    contract = slither.get_contract_from_name("RepeatedFields")[0]
    for name, expected in REPEATED_FIELD_SIGNATURES.items():
        function = contract.get_function_from_signature(expected)
        assert function is not None, f"{expected} is not resolvable from its canonical signature"
        assert function.name == name
        assert function.solidity_signature == expected
