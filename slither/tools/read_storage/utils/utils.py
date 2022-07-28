from typing import Union, Type, List, Optional
from hexbytes import HexBytes
from eth_typing.evm import ChecksumAddress
from eth_utils import to_int, to_text, to_checksum_address


def get_offset_value(hex_bytes: HexBytes, offset: int, size: int) -> bytes:
    """
    Trims slot data to only contain the target variable's.
    Args:
        hex_bytes (HexBytes): String representation of type
        offset (int): The size (in bits) of other variables that share the same slot.
        size (int): The size (in bits) of the target variable.
    Returns:
        (bytes): The target variable's trimmed data.
    """
    size = int(size / 8)
    offset = int(offset / 8)
    if offset == 0:
        value = hex_bytes[-size:]
    else:
        start = size + offset
        value = hex_bytes[-start:-offset]
    return value


def coerce_type(solidity_type: str, value: bytes) -> Union[int, bool, str, ChecksumAddress]:
    """
    Converts input to the indicated type.
    Args:
        solidity_type (str): String representation of type.
        value (bytes): The value to be converted.
    Returns:
        (Union[int, bool, str, ChecksumAddress, hex]): The type representation of the value.
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
    Args:
        web3: Web3 instance provider.
        checksum_address (ChecksumAddress): The address to query.
        slot (bytes): The slot to retrieve data from.
    Returns:
        (HexBytes): The slot's storage data.
    """
    return bytes(web3.eth.get_storage_at(checksum_address, slot)).rjust(
        32, bytes(1)
    )  # pad to 32 bytes
