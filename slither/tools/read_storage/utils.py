from typing import Union
from hexbytes import HexBytes
from eth_typing.evm import ChecksumAddress
from eth_utils import to_int, to_text, to_checksum_address

from slither.core.declarations import Structure, Enum
from slither.core.solidity_types import ArrayType, MappingType, UserDefinedType
from slither.core.variables.state_variable import StateVariable

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

def coerce_type(solidity_type: str, value: bytes) -> Union[int, bool, str, ChecksumAddress, hex]:
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

def get_storage_data(web3, checksum_address: ChecksumAddress, slot: bytes) -> HexBytes:
    """
    Retrieves the storage data from the blockchain at target address and slot.
    :param web3: Web3 instance provider.
    :param checksum_address: The address to query.
    :param slot: The slot to retrieve data from.
    :return: Returns the slot's storage data.
    """
    return web3.eth.get_storage_at(checksum_address, slot)