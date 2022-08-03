from solc_select import solc_select
from slither import Slither

# % solc functions_ids.sol --hashes
# ======= functions_ids.sol:C =======
# Function signatures:
# 0dbe671f: a()
# 4a1f689d: a_array(uint256)
# 98fc2aa5: arrayOfMappings(uint256,uint256)
# 4ea7a557: b_mapping_of_array(address,uint256)
# 3c0af344: contractMap(address)
# 20969954: function_with_array(((uint256,uint256),uint256)[],(uint256,(uint256,uint256)))
# 1c039831: function_with_struct(((uint256,uint256),uint256))
# 37e66bae: mapping_of_double_array_of_struct(address,uint256,uint256)
# f29872a8: multiDimensionalArray(uint256,uint256)
# 9539e3c8: normalMappingArrayField(uint256,uint256)
# 87c3dbb6: outer()
# df201a46: simple()
# 5a20851f: stateMap(uint16)

# {"contracts":{"functions_ids.sol:C":{"hashes":{"a()":"0dbe671f","a_array(uint256)":"4a1f689d","arrayOfMappings(uint256,uint256)":"98fc2aa5","b_mapping_of_array(address,uint256)":"4ea7a557","contractMap(address)":"3c0af344","function_with_array(((uint256,uint256),uint256)[],(uint256,(uint256,uint256)))":"20969954","function_with_struct(((uint256,uint256),uint256))":"1c039831","mapping_of_double_array_of_struct(address,uint256,uint256)":"37e66bae","multiDimensionalArray(uint256,uint256)":"f29872a8","normalMappingArrayField(uint256,uint256)":"9539e3c8","outer()":"87c3dbb6","simple()":"df201a46","stateMap(uint16)":"5a20851f"}},"functions_ids.sol:Contract":{"hashes":{}}},"version":"0.7.0+commit.9e61f92b.Darwin.appleclang"}
from slither.utils.function import get_function_id

signatures = {
    "a()": "0dbe671f",
    "a_array(uint256)": "4a1f689d",
    "arrayOfMappings(uint256,uint256)": "98fc2aa5",
    "b_mapping_of_array(address,uint256)": "4ea7a557",
    "contractMap(address)": "3c0af344",
    "function_with_array(((uint256,uint256),uint256)[],(uint256,(uint256,uint256)))": "20969954",
    "function_with_struct(((uint256,uint256),uint256))": "1c039831",
    "mapping_of_double_array_of_struct(address,uint256,uint256)": "37e66bae",
    "multiDimensionalArray(uint256,uint256)": "f29872a8",
    "normalMappingArrayField(uint256,uint256)": "9539e3c8",
    "outer()": "87c3dbb6",
    "simple()": "df201a46",
    "stateMap(uint16)": "5a20851f",
}


def test_functions_ids() -> None:
    solc_select.switch_global_version("0.7.0")
    sl = Slither("tests/printers/functions_ids.sol")
    contracts_c = sl.get_contract_from_name("C")
    assert len(contracts_c) == 1
    contract_c = contracts_c[0]

    for sig, hashes in signatures.items():
        func = contract_c.get_function_from_signature(sig)
        if not func:
            var_name = sig[: sig.find("(")]
            var = contract_c.get_state_variable_from_name(var_name)
            assert var
            assert get_function_id(var.solidity_signature) == int(hashes, 16)
        else:
            assert get_function_id(func.solidity_signature) == int(hashes, 16)


if __name__ == "__main__":
    test_functions_ids()
