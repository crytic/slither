import sys
import json
import logging
from math import floor

from typing import Any, Union, List
from hexbytes import HexBytes

from slither.core.solidity_types.type import Type


try:
    from web3 import Web3
    from eth_typing.evm import ChecksumAddress
    from eth_abi import decode_single, encode_abi
    from eth_utils import keccak, to_int, to_text, to_checksum_address
except ImportError:
    print("ERROR: in order to use slither-read-storage, you need to install web3")
    print("$ pip3 install web3 --user\n")
    sys.exit(-1)

from slither import Slither
from slither.core.declarations import Structure, Enum, Contract
from slither.core.solidity_types import ArrayType, MappingType, UserDefinedType
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.structure_variable import StructureVariable

logging.basicConfig()
logger = logging.getLogger("Slither-read-storage")
logger.setLevel(logging.INFO)


class SlitherReadStorageException(Exception):
    pass


def get_storage_layout(contracts: List[Contract], address: str, storage_address: str = None, **kwargs):
    data = {}
    for state_var in _all_storage_variables(contracts):

        tmp = {}
        for contract, var, type_ in state_var:
            slot, val, type_string = get_storage_slot_and_val(
                contracts, address, storage_address, **(dict(kwargs, variable_name=var))
            )
            tmp[var] = {"slot": slot, "value": val, "type_string": type_string}

            if is_array(type_):
                if type_.is_fixed_array:  # arr[i]
                    val = int(str(type_.length))
                if isinstance(val, str):  # arr[i][]
                    val = int(
                        val, 16
                    )  # the length of dynamic arrays is stored at the starting slot

                elems = {}
                for i in range(val):
                    slot, val, type_string = get_storage_slot_and_val(
                        contracts,
                        address,
                        storage_address,
                        **(dict(kwargs, variable_name=var, key=str(i))),
                    )
                    elems[i] = {"slot": slot, "value": val, "type_string": type_string, "val": val}

                    if is_array(type_.type):
                        if type_.type.is_fixed_array:  # arr[i][]
                            val = int(str(type_.type.length))
                        if isinstance(val, str):  # arr[][i]
                            val = int(
                                val, 16
                            )  # the length of dynamic arrays is stored at the starting slot

                        elems[i]["elems"] = {}
                        for j in range(val):
                            slot, value, type_string = get_storage_slot_and_val(
                                contracts,
                                address,
                                storage_address,
                                **(dict(kwargs, variable_name=var, key=str(i), deep_key=str(j))),
                            )
                            elems[i]["elems"][j] = {
                                "slot": slot,
                                "value": value,
                                "type_string": type_string,
                                "val": f"[{type_.type.is_fixed_array}]"
                            }

                tmp[var]["elems"] = elems

        data[contract] = tmp

    with open(f"{address}_storage_layout.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def get_storage_slot_and_val(
    contracts: List[Contract], address: str, storage_address: str = None, **kwargs
) -> Union[bytes, Any]:
    """Finds the storage slot of a variable in a contract by its name and retrieves the slot and data.
    Args:
        - slither (Slither): Slither analyzer object for target address.
        - address (str): The address of the implementation contract.
        - variable_name (str) : The variable to retrieve the slot and data for.
        - rpc_url (str) : HTTP url to establish web3 provider.
        - storage_address (str) : The address of the storage contract (if a proxy pattern is used).
    Keyword Args:
        - key (str) - Key of a mapping or position if an array.
        - deep_key (str) - Key of a mapping embedded within another mapping.
        - struct_var (str) - Structure variable name.
    Returns:
        - slot (bytes) - The storage location of the variable.
        - value (Any) - The type representation of the variable's data.
    Raises
        SlitherReadStorageException: if the variable is not found.
    """

    if ":" in address:
        address = address[address.find(":") + 1 :]  # Remove target prefix e.g. rinkeby:0x0 -> 0x0
    if not storage_address:
        storage_address = (
            address  # Default to implementation address unless a storage address is given
        )

    variable_name = kwargs.get("variable_name", None)
    contract_name = kwargs.get("contract_name", None)
    rpc_url = kwargs.get("rpc_url")
    key = kwargs.get("key", None)
    deep_key = kwargs.get("deep_key", None)
    struct_var = kwargs.get("struct_var", None)

    found = False
    var_log_name = variable_name

    for contract in contracts:
        # Find all instances of the variable in the target contract(s)
        if variable_name in contract.variables_as_dict:
            contract_name = contract.name
            found = True
            target_variable = contract.variables_as_dict[variable_name]

            if (
                target_variable.is_constant or target_variable.is_immutable
            ):  # Variable with same name may exist in multiple contracts so continue rather than raising exception
                logger.info(
                    "The solidity compiler does not reserve storage for constants or immutables"
                )
                continue

            web3: Web3 = Web3(Web3.HTTPProvider(rpc_url))
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

            except KeyError:  # Only the child contract of a parent contract will show up in the storage layout when inheritance is used
                logger.info(
                    f"Contract {contract} not found in storage layout. It is possibly a parent contract"
                )
                continue

            # Traverse the data structure of the target variable, return early if user does not provide key/ deep key/ struct var
            if is_array(target_variable.type):
                if key:
                    info, type_to, slot, size, offset = find_array_slot(
                        target_variable, slot, key, deep_key=deep_key
                    )
                    log += info
                else:
                    return (
                        int.from_bytes(slot, byteorder="big"),
                        get_storage_data(web3, checksum_address, slot).hex(),
                        type_to,
                    )

            elif is_user_defined_type(target_variable.type):
                if struct_var:
                    var_log_name = struct_var
                    type_to = target_variable.type.type.name
                    elems = target_variable.type.type.elems_ordered
                    info, type_to, slot, size, offset = find_struct_var_slot(
                        elems, slot, struct_var
                    )
                    log += info
                else:
                    return (
                        int.from_bytes(slot, byteorder="big"),
                        get_storage_data(web3, checksum_address, slot).hex(),
                        type_to,
                    )

            elif is_mapping(target_variable.type):
                if key:
                    info, type_to, slot, size, offset = find_mapping_slot(
                        target_variable, slot, key, struct_var=struct_var, deep_key=deep_key
                    )
                    log += info
                else:
                    return (
                        int.from_bytes(slot, byteorder="big"),
                        get_storage_data(web3, checksum_address, slot).hex(),
                        type_to,
                    )

            else:  # elementary type
                type_to = target_variable.type.name

            hex_bytes = get_storage_data(web3, checksum_address, slot)
            offset_hex_bytes = get_offset_value(
                hex_bytes, offset, size
            )  # account for storage packing

            value = coerce_type(type_to, offset_hex_bytes)
            log += f"\nName: {var_log_name}\nType: {type_to}\nValue: {value}\nSlot: {int.from_bytes(slot, byteorder='big')}\n"
            logger.info(log)

            return int.from_bytes(slot, byteorder="big"), value, type_to

    if not found:
        raise SlitherReadStorageException("%s was not found in %s" % (variable_name, address))


def get_offset_value(hex_bytes: HexBytes, offset: int, size: int) -> HexBytes:
    """
    Trims slot data to only contain the target variable's.
    :param hex_bytes: String representation of type
    :param offset: The size (in bits) of other variables that share the same slot.
    :param size: The size (in bits) of the target variable.
    :return: The target variable's data.
    """
    size = int(size / 8)
    offset = int(offset / 8)
    if offset == 0:
        value = hex_bytes[-size:]
    else:
        start = size + offset
        value = hex_bytes[-start:-offset]
    return value


def get_slot(key_type: str, slot: bytes, key: Any) -> bytes:
    """
    Calculates the data slot of mapping[key].
    :param key_type: The type of the key e.g. address or uint
    :param slot: The starting slot of the mapping.
    :param key: The target key.
    :return: Returns the slot of key's data.
    """
    slot = keccak(encode_abi([key_type, "uint256"], [key, decode_single("uint256", slot)]))
    return slot


def coerce_type(solidity_type: str, value: bytes) -> Any:
    """
    Converts input to the indicated type.
    :param solidity_type: String representation of type.
    :param value: The value to be converted.
    :return: Returns the type representation of the value.
    """
    if "int" in solidity_type:
        converted_value = to_int(value)
    elif "bool" in solidity_type:
        converted_value = bool(to_int(value))
    elif "string" in solidity_type:
        # length * 2 is stored in lower end bits
        # TODO handle bytes and strings greater than 32 bytes
        length = int(int.from_bytes(value[-2:], "big") / 2)
        converted_value = to_text(value[:length])

    elif "address" in solidity_type:
        converted_value = to_checksum_address(value)
    else:
        converted_value = value.hex()

    return converted_value


def find_struct_var_slot(
    elems: List[StructureVariable], slot: bytes, struct_var: str
) -> Union[str, bytes, int, int]:
    """
    Finds the slot of a structure variable.
    :param elems: Ordered list of structure variables to search through.
    :param slot: The slot of the struct to begin searching at.
    :param struct_var: The target structure variable.
    :returns:
        - info - Info about the target variable to log.
        - type_to - The type of the target variable.
        - slot - The storage location of the target variable.
        - size - The size (in bits) of the target variable.
        - offset - The size of other variables that share the same slot.
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


def find_array_slot(
    target_variable: StateVariable, slot: bytes, key: int, deep_key=None, struct_var=None
) -> Union[str, bytes]:
    """
    Finds the slot of array's index.
    :param target_variable: The array that contains the target variable.
    :param slot: The starting slot of the array.
    :param key: The target variable's index position.
    :returns:
        - info - Info about the target variable to log.
        - type_to - The type of the target variable.
        - slot - The storage location of the target variable.
    """
    info = f"\nKey: {key}"
    offset = 0
    print(dir(target_variable.type.type), target_variable.type.is_fixed_array)
    if is_array(
        target_variable.type.type
    ):  # multidimensional array uint[i][], , uint[][i], or uint[][]
        size = target_variable.type.type.type.size
        type_to = target_variable.type.type.type.name

        if target_variable.type.is_fixed_array:  # uint[][i]
            print("here")
            slot_int = int.from_bytes(slot, "big") + int(key)
        else:
            print("here2")
            slot = keccak(slot)
            key = int(key)
            if target_variable.type.type.is_fixed_array:  # arr[i][]
                key *= int(str(target_variable.type.type.length))
                print(key)
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
        print(is_user_defined_type(target_variable.type.type))
        print(is_struct(target_variable.type.type))
        if is_user_defined_type(target_variable.type.type):  # struct[i]
            size = 32
            type_to = target_variable.type.type.type.name
            if not struct_var:
                return info, type_to, int.to_bytes(slot_int, 32, "big"), size, offset
            elems = target_variable.type.type.elems_ordered
            slot = int.to_bytes(slot_int, 32, byteorder="big")
            info_tmp, type_to, slot, size, offset = find_struct_var_slot(elems, slot, struct_var)
            slot_int = int.from_bytes(slot, "big")
            info += info_tmp

        else:
            type_to = target_variable.type.type.name
            size = target_variable.type.type.size  # bits

    else:
        slot = keccak(slot)
        slot_int = int.from_bytes(slot, "big") + int(key)
        type_to = target_variable.type.type.name
        size = target_variable.type.type.size  # bits

    slot = int.to_bytes(slot_int, 32, byteorder="big")

    return info, type_to, slot, size, offset


def find_mapping_slot(
    target_variable: StateVariable, slot: bytes, key: Any, struct_var=None, deep_key=None
) -> Union[str, bytes, int, int]:
    """
    Finds the data slot of a target variable within a mapping.
    :param target_variable: The array that contains the target variable.
    :param slot: The starting slot of the array.
    :param key: The key the variable is stored at.
    :returns:
        - log - Info about the target variable to log.
        - type_to - The type of the target variable.
        - slot - The storage location of the target variable.
        - size - The size (in bits) of the target variable.
        - offset - The size of other variables that share the same slot.

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
    slot = get_slot(key_type, slot, key)

    if is_user_defined_type(target_variable.type.type_to) and is_struct(
        target_variable.type.type_to.type
    ):  # mapping(elem => struct)
        assert struct_var
        elems = target_variable.type.type_to.type.elems_ordered
        info_tmp, type_to, slot, size, offset = find_struct_var_slot(elems, slot, struct_var)
        info += info_tmp

    elif is_mapping(target_variable.type.type_to):  # mapping(elem => mapping(elem => ???))
        assert deep_key
        deep_key_type = target_variable.type.type_to.type_from.name
        if "int" in deep_key_type:  # without this eth_utils encoding fails
            deep_key = int(deep_key)
        # if deep map, will be keccak256(abi.encode(key1, keccak256(abi.encode(key0, uint(slot)))));
        slot = keccak(
            encode_abi([deep_key_type, "bytes32"], [deep_key, slot])
        )  # mapping(elem => mapping(elem => elem))
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
            info_tmp, type_to, slot, size, offset = find_struct_var_slot(elems, slot, struct_var)
            info += info_tmp

    else:  # mapping(elem => elem)
        type_to = target_variable.type.type_to.name  # the value's elementary type
        byte_size, _ = target_variable.type.type_to.storage_size
        size = byte_size * 8  # bits

    return info, type_to, slot, size, offset


def get_storage_data(web3, checksum_address: ChecksumAddress, slot: bytes) -> HexBytes:
    """
    Retrieves the storage data from the blockchain at target address and slot.
    :param web3: Web3 instance provider.
    :param checksum_address: The address to query.
    :param slot: The slot to retrieve data from.
    :return: Returns the slot's storage data.
    """
    return web3.eth.get_storage_at(checksum_address, slot)


def is_array(variable: StateVariable) -> bool:
    """Returns whether variable is an array."""
    return isinstance(variable, ArrayType)


def is_mapping(variable: StateVariable) -> bool:
    """Returns whether variable is a mapping."""
    return isinstance(variable, MappingType)


def is_struct(variable: StateVariable) -> bool:
    """Returns whether variable is a struct."""
    return isinstance(variable, Structure)


def is_enum(variable: StateVariable) -> bool:
    """Returns whether variable is an enum."""
    return isinstance(variable, Enum)


def is_user_defined_type(variable: StateVariable) -> bool:
    """Returns whether variable is a struct."""
    return isinstance(variable, UserDefinedType)


def _all_storage_variables(contracts: List[Contract]) -> List[Union[str, str, Type]]:
    storage_variables = []
    for contract in contracts:
        storage_variables.append([(contract.name, var.name, var.type)
            for var in contract.variables
            if not var.is_constant and not var.is_immutable
        ])
        
    return storage_variables