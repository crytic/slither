import sys
import json
import logging
from math import floor

from typing import Any, Tuple, Union, List

try:
    from web3 import Web3
    from eth_typing.evm import ChecksumAddress
    from eth_abi import decode_single, encode_abi
    from eth_utils import keccak
    from .utils import (
        is_array,
        is_mapping,
        is_struct,
        is_user_defined_type,
        get_offset_value,
        get_storage_data,
        coerce_type,
    )
except ImportError:
    print("ERROR: in order to use slither-read-storage, you need to install web3")
    print("$ pip3 install web3 --user\n")
    sys.exit(-1)

from slither.core.declarations import Contract, StructureContract
from slither.core.solidity_types.type import Type
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.structure_variable import StructureVariable


logging.basicConfig()
logger = logging.getLogger("Slither-read-storage")
logger.setLevel(logging.INFO)


class SlitherReadStorageException(Exception):
    pass


# pylint: disable=too-many-arguments
def _all_struct_variables(var, contracts, address, rpc_url, storage_address=None, key=None):
    """Retrieves all members of a struct."""
    if isinstance(var.type.type, StructureContract):
        struct_elems = var.type.type.elems_ordered
    else:
        struct_elems = var.type.type.type.elems_ordered
    data = {}
    for _, elem in enumerate(struct_elems):
        slot, val, type_string = get_storage_slot_and_val(
            contracts,
            address,
            var.name,
            rpc_url,
            storage_address,
            key=key,
            struct_var=elem.name,
        )
        data[elem.name] = {"slot": slot, "value": val, "type_string": type_string}

    return data


# pylint: disable=too-many-branches,too-many-locals,too-many-nested-blocks
def get_storage_layout(
    contracts: List[Contract],
    address: str,
    rpc_url: str,
    max_depth: int,
    storage_address: str = None,
):
    """Retrieves the storage layout of a contract and writes it to a JSON file.
    Args:
        contracts (List[`Contract`]): List of contracts from a slither analyzer object.
        address (str): The address of the implementation contract.
        rpc_url (str): HTTP url to establish web3 provider.
        max_depth (int): The maximum depth to search through a data structure.
        storage_address (str, optional): The address of the storage contract (if a proxy pattern is used).
    """

    data = {}
    for state_var in _all_storage_variables(contracts):

        tmp = {}
        for contract, var in state_var:
            var_name = var.name
            type_ = var.type
            slot, val, type_string = get_storage_slot_and_val(
                contracts, address, var_name, rpc_url, storage_address
            )

            tmp[var_name] = {"slot": slot, "value": val, "type_string": type_string}

            if is_user_defined_type(type_) and is_struct(type_.type):
                tmp[var_name]["elems"] = _all_struct_variables(
                    var, contracts, address, rpc_url, storage_address
                )
                continue

            if is_array(type_):
                if type_.is_fixed_array:  # arr[i]
                    val = int(str(type_.length))

                if isinstance(val, str):  # arr[] or arr[i][]
                    # The length of dynamic arrays is stored at the starting slot
                    val = int(val, 16)

                elems = {}
                if is_user_defined_type(type_.type):
                    for i in range(min(val, max_depth)):
                        elems[i] = _all_struct_variables(
                            var, contracts, address, rpc_url, storage_address, key=str(i)
                        )
                        continue

                else:
                    for i in range(min(val, max_depth)):
                        slot, val, type_string = get_storage_slot_and_val(
                            contracts,
                            address,
                            var_name,
                            rpc_url,
                            storage_address,
                            key=str(i),
                        )
                        elems[i] = {"slot": slot, "value": val, "type_string": type_string}

                        if is_array(type_.type):
                            if type_.type.is_fixed_array:  # arr[i][]
                                val = int(str(type_.type.length))
                            if isinstance(val, str):  # arr[][i]
                                # The length of dynamic arrays is stored at the starting slot
                                val = int(val, 16)

                            elems[i]["elems"] = {}
                            for j in range(min(val, max_depth)):
                                slot, value, type_string = get_storage_slot_and_val(
                                    contracts,
                                    address,
                                    var_name,
                                    rpc_url,
                                    storage_address,
                                    key=str(i),
                                    deep_key=str(j),
                                )
                                elems[i]["elems"][j] = {
                                    "slot": slot,
                                    "value": value,
                                    "type_string": type_string,
                                }

                tmp[var_name]["elems"] = elems

            data[contract] = tmp

    with open(f"{address}_storage_layout.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# pylint: disable=too-many-statements,too-many-branches,inconsistent-return-statements
def get_storage_slot_and_val(
    contracts: List[Contract],
    address: str,
    var_name: str,
    rpc: str,
    storage_address: str = None,
    **kwargs,
) -> Tuple[int, Any, str]:
    """Finds the storage slot of a variable in a contract by its name and retrieves the slot and data.
    Args:
        contracts (List[`Contract`]): List of contracts from a slither analyzer object.
        address (str): The address of the implementation contract.
        var_name (str): The variable to retrieve the slot and data for.
        rpc (str): HTTP url to establish web3 provider.
        storage_address (str, optional): The address of the storage contract (if a proxy pattern is used).
    **kwargs:
        key (str): Key of a mapping or index position if an array.
        deep_key (str): Key of a mapping embedded within another mapping or secondary index if array.
        struct_var (str): Structure variable name.
    Returns:
        slot (int): The storage location of the variable.
        value (Any): The type representation of the variable's data.
        type_to (str): What type the variable is.
    Raises:
        SlitherReadStorageException: if the variable is not found.
    """

    if not storage_address:
        storage_address = (
            address  # Default to implementation address unless a storage address is given
        )

    key = kwargs.get("key", None)
    deep_key = kwargs.get("deep_key", None)
    struct_var = kwargs.get("struct_var", None)

    found = False
    var_log_name = var_name

    for contract in contracts:
        # Find all instances of the variable in the target contract(s)
        if var_name in contract.variables_as_dict:
            contract_name = contract.name
            found = True
            target_variable = contract.variables_as_dict[var_name]

            if (
                target_variable.is_constant or target_variable.is_immutable
            ):  # Variable with same name may exist in multiple contracts so continue rather than raising exception
                logger.info(
                    "The solidity compiler does not reserve storage for constants or immutables"
                )
                continue

            web3: Web3 = Web3(Web3.HTTPProvider(rpc))
            checksum_address: ChecksumAddress = web3.toChecksumAddress(storage_address)
            type_to = str(target_variable.type)
            log = ""

            try:
                byte_size, _ = target_variable.type.storage_size
                size = byte_size * 8  # bits
                (slot_int, offset) = contract.compilation_unit.storage_layout_of(
                    contract, target_variable
                )
                offset *= 8  # bits
                slot = int.to_bytes(slot_int, 32, "big")
                hex_bytes = get_storage_data(web3, checksum_address, slot)
                logger.info(
                    f"\nContract '{contract_name}'\n{target_variable.canonical_name} with type {target_variable.type} evaluated to:\n{(hex_bytes.hex())}\nSlot: {slot_int}\n"
                )

            except KeyError:
                # Only the child contract of a parent contract will show up in the storage layout when inheritance is used
                logger.info(
                    f"Contract {contract} not found in storage layout. It is possibly a parent contract"
                )
                continue

            # Traverse the data structure of the target variable, return early if user does not provide key/ deep key/ struct var
            if is_array(target_variable.type):
                if key:
                    info, type_to, slot, size, offset = _find_array_slot(
                        target_variable, slot, key, deep_key=deep_key, struct_var=struct_var
                    )
                    log += info
                else:
                    value = get_storage_data(web3, checksum_address, slot).hex()
                    int_slot = int.from_bytes(slot, byteorder="big")
                    return (
                        int_slot,
                        value,
                        type_to,
                    )

            elif is_user_defined_type(target_variable.type):
                if struct_var:
                    var_log_name = struct_var
                    elems = target_variable.type.type.elems_ordered
                    info, type_to, slot, size, offset = _find_struct_var_slot(
                        elems, slot, struct_var
                    )
                    log += info
                else:
                    value = get_storage_data(web3, checksum_address, slot).hex()
                    int_slot = int.from_bytes(slot, byteorder="big")
                    return (
                        int_slot,
                        value,
                        type_to,
                    )

            elif is_mapping(target_variable.type):
                if key:
                    info, type_to, slot, size, offset = _find_mapping_slot(
                        target_variable, slot, key, struct_var=struct_var, deep_key=deep_key
                    )
                    log += info
                else:
                    value = get_storage_data(web3, checksum_address, slot).hex()
                    int_slot = int.from_bytes(slot, byteorder="big")
                    return (
                        int_slot,
                        value,
                        type_to,
                    )

            else:  # elementary type
                type_to = target_variable.type.name

            hex_bytes = get_storage_data(web3, checksum_address, slot)
            int_slot = int.from_bytes(slot, byteorder="big")

            # Account for storage packing
            offset_hex_bytes = get_offset_value(hex_bytes, offset, size)
            value = coerce_type(type_to, offset_hex_bytes)

            log += f"\nName: {var_log_name}\nType: {type_to}\nValue: {value}\nSlot: {int.from_bytes(slot, byteorder='big')}\n"
            logger.info(log)

            return int_slot, value, type_to

    if not found:
        raise SlitherReadStorageException("%s was not found in %s" % (var_name, address))


def _find_struct_var_slot(
    elems: List[StructureVariable], slot: bytes, struct_var: str
) -> Tuple[str, str, bytes, int, int]:
    """Finds the slot of a structure variable.
    Args:
        elems (List[StructureVariable]): Ordered list of structure variables.
        slot (bytes): The slot of the struct to begin searching at.
        struct_var (str): The target structure variable.
    Returns:
        info (str): Info about the target variable to log.
        type_to (str): The type of the target variable.
        slot (bytes): The storage location of the target variable.
        size (int): The size (in bits) of the target variable.
        offset (int): The size of other variables that share the same slot.
    """
    slot = int.from_bytes(slot, "big")
    offset = 0
    for var in elems:
        size = var.type.size
        if offset >= 256:
            slot += 1
            offset = 0
        if struct_var == var.name:
            type_to = var.type.name
            break  # found struct var
        offset += size

    slot = int.to_bytes(slot, 32, byteorder="big")
    info = f"\nStruct Variable: {struct_var}"
    return info, type_to, slot, size, offset


# pylint: disable=too-many-statements,too-many-branches
def _find_array_slot(
    target_variable: StateVariable,
    slot: bytes,
    key: int,
    deep_key: int = None,
    struct_var: str = None,
) -> Tuple[str, str, bytes]:
    """Finds the slot of array's index.
    Args:
        target_variable (`StateVariable`): The array that contains the target variable.
        slot (bytes): The starting slot of the array.
        key (int): The target variable's index position.
        deep_key (int, optional): Key of a mapping embedded within another mapping or secondary index if array.
        struct_var (str, optional): Structure variable name.
    Returns:
        info (str): Info about the target variable to log.
        type_to (str): The type of the target variable.
        slot (bytes): The storage location of the target variable.
    """
    info = f"\nKey: {key}"
    offset = 0
    if is_array(
        target_variable.type.type
    ):  # multidimensional array uint[i][], , uint[][i], or uint[][]
        size = target_variable.type.type.type.size
        type_to = target_variable.type.type.type.name

        if target_variable.type.is_fixed_array:  # uint[][i]
            slot_int = int.from_bytes(slot, "big") + int(key)
        else:
            slot = keccak(slot)
            key = int(key)
            if target_variable.type.type.is_fixed_array:  # arr[i][]
                key *= int(str(target_variable.type.type.length))
            slot_int = int.from_bytes(slot, "big") + key

        if not deep_key:
            return info, type_to, int.to_bytes(slot_int, 32, "big"), size, offset

        info += f"\nDeep Key: {deep_key}"
        if target_variable.type.type.is_dynamic_array:  # uint[][]
            # keccak256(keccak256(slot) + index) + floor(j / floor(256 / size))
            slot = keccak(int.to_bytes(slot_int, 32, "big"))
            slot_int = int.from_bytes(slot, "big")

        # keccak256(slot) + index + floor(j / floor(256 / size))
        slot_int += floor(int(deep_key) / floor(256 / size))  # uint[i][]

    elif target_variable.type.is_fixed_array:
        slot_int = int.from_bytes(slot, "big") + int(key)
        if is_user_defined_type(target_variable.type.type):  # struct[i]
            size = 256
            type_to = target_variable.type.type.type.name
            if not struct_var:
                return info, type_to, int.to_bytes(slot_int, 32, "big"), size, offset
            elems = target_variable.type.type.type.elems_ordered
            slot = int.to_bytes(slot_int, 32, byteorder="big")
            info_tmp, type_to, slot, size, offset = _find_struct_var_slot(elems, slot, struct_var)
            slot_int = int.from_bytes(slot, "big")
            info += info_tmp

        else:
            type_to = target_variable.type.type.name
            size = target_variable.type.type.size  # bits

    elif is_user_defined_type(target_variable.type.type):  # struct[]
        slot = keccak(slot)
        slot_int = int.from_bytes(slot, "big") + int(key)
        size = 256
        type_to = target_variable.type.type.type.name
        if not struct_var:
            return info, type_to, int.to_bytes(slot_int, 32, "big"), size, offset
        elems = target_variable.type.type.type.elems_ordered
        slot = int.to_bytes(slot_int, 32, byteorder="big")
        info_tmp, type_to, slot, size, offset = _find_struct_var_slot(elems, slot, struct_var)
        slot_int = int.from_bytes(slot, "big")
        info += info_tmp

    else:
        slot = keccak(slot)
        slot_int = int.from_bytes(slot, "big") + int(key)
        type_to = target_variable.type.type.name
        size = target_variable.type.type.size  # bits

    slot = int.to_bytes(slot_int, 32, byteorder="big")

    return info, type_to, slot, size, offset


def _find_mapping_slot(
    target_variable: StateVariable,
    slot: bytes,
    key: Union[int, str],
    deep_key: Union[int, str] = None,
    struct_var: str = None,
) -> Tuple[str, str, bytes, int, int]:
    """Finds the data slot of a target variable within a mapping.
        target_variable (`StateVariable`): The array that contains the target variable.
        slot (bytes): The starting slot of the array.
        key (Union[int, str]): The key the variable is stored at.
        deep_key (int, optional): Key of a mapping embedded within another mapping or secondary index if array.
        struct_var (str, optional): Structure variable name.
    :returns:
        log (str): Info about the target variable to log.
        type_to (bytes): The type of the target variable.
        slot (bytes): The storage location of the target variable.
        size (int): The size (in bits) of the target variable.
        offset (int): The size of other variables that share the same slot.

    """
    info = ""
    if key:
        info += f"\nKey: {key}"
    if deep_key:
        info += f"\nDeep Key: {deep_key}"

    key_type = target_variable.type.type_from.name
    assert key
    if "int" in key_type:  # without this eth_utils encoding fails
        key = int(key)
    key = coerce_type(key_type, key)
    slot = keccak(encode_abi([key_type, "uint256"], [key, decode_single("uint256", slot)]))

    if is_user_defined_type(target_variable.type.type_to) and is_struct(
        target_variable.type.type_to.type
    ):  # mapping(elem => struct)
        assert struct_var
        elems = target_variable.type.type_to.type.elems_ordered
        info_tmp, type_to, slot, size, offset = _find_struct_var_slot(elems, slot, struct_var)
        info += info_tmp

    elif is_mapping(target_variable.type.type_to):  # mapping(elem => mapping(elem => ???))
        assert deep_key
        deep_key_type = target_variable.type.type_to.type_from.name
        if "int" in deep_key_type:  # without this eth_utils encoding fails
            deep_key = int(deep_key)

        # If deep map, will be keccak256(abi.encode(key1, keccak256(abi.encode(key0, uint(slot)))))
        slot = keccak(encode_abi([deep_key_type, "bytes32"], [deep_key, slot]))

        # mapping(elem => mapping(elem => elem))
        type_to = target_variable.type.type_to.type_to.type
        byte_size, _ = target_variable.type.type_to.type_to.storage_size
        size = byte_size * 8  # bits
        offset = 0

        if is_user_defined_type(target_variable.type.type_to.type_to) and is_struct(
            target_variable.type.type_to.type_to.type
        ):  # mapping(elem => mapping(elem => struct))
            assert struct_var
            elems = target_variable.type.type_to.type_to.type.elems_ordered
            # if map struct, will be bytes32(uint256(keccak256(abi.encode(key1, keccak256(abi.encode(key0, uint(slot)))))) + structFieldDepth);
            info_tmp, type_to, slot, size, offset = _find_struct_var_slot(elems, slot, struct_var)
            info += info_tmp

    else:  # mapping(elem => elem)
        type_to = target_variable.type.type_to.name  # the value's elementary type
        byte_size, _ = target_variable.type.type_to.storage_size
        size = byte_size * 8  # bits

    return info, type_to, slot, size, offset


def _all_storage_variables(contracts: List[Contract]) -> List[Tuple[str, str, Type]]:
    """Fetches all storage variables from a list of contracts.
    Args:
        contracts (List[`Contract`]): The contract from which to retrieve storage variables.
    Returns:
        List of tuples contain state variable info (contract_name, var).
    """
    storage_variables = []
    for contract in contracts:
        storage_variables.append(
            [
                (contract.name, var)
                for var in contract.variables
                if not var.is_constant and not var.is_immutable
            ]
        )

    return storage_variables
