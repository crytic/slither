import pytest

from slither.tools.read_storage.read_storage import SlitherReadStorage


@pytest.mark.parametrize(
    ("name", "key", "deep_key", "expected_slot"),
    [
        ("single", 0, None, 0xA6EEF7E35ABE7026729641147F7915573C7E97B47EFA546F5F6E3230263BCB49),
        ("single", "0", None, 0xA6EEF7E35ABE7026729641147F7915573C7E97B47EFA546F5F6E3230263BCB49),
        ("nested", 0, 1, 0x79C06E8C99A667ADDA63C5FA6F05695D29630FC62AD2DD069FA929D5714DE89D),
        ("nested", 1, 0, 0xF8DD1754CDB399BC5B4E203E4ACFEC383074082A262A94D223F4E1BA300EAF08),
        ("matrix", 0, 0, 0x2584DB4A68AA8B172F70BC04E2E74541617C003374DE6EB4B295E823E5BEAB01),
    ],
    ids=["zero", "string-zero", "outer-zero", "inner-zero", "nested-array-zero"],
)
def test_zero_storage_keys(slither_from_solidity_source, name, key, deep_key, expected_slot):
    source = """
pragma solidity 0.8.19;
contract C {
    uint256 guard;
    mapping(uint256 => uint256) single;
    mapping(uint256 => mapping(uint256 => uint256)) nested;
    uint256[][] matrix;
}
"""
    with slither_from_solidity_source(source) as slither:
        contract = slither.get_contract_from_name("C")[0]
        storage = SlitherReadStorage([contract], max_depth=20)
        variable = contract.get_state_variable_from_name(name)
        info = storage.get_storage_slot(variable, contract, key=key, deep_key=deep_key)
        assert info.slot == expected_slot
        assert info.type_string == "uint256"
