def get_offset_value(hex_bytes, offset, size):
    print(f"size : {size}")
    if offset == 0:
        return hex_bytes[-size:]
    else:
        start = size + offset
        return hex_bytes[-start:-offset]


def convert_hex_bytes_to_type(web3, hex_bytes, type):
    """
    Obtains all functions which can lead to any of the target functions being called.
    :param web3: web3 provider instance
    :param hex_bytes: value returned by web3.getStorageAt([address], [slot])
    :param type: string representation of type
    :return: Returns a list of all functions which can reach any of the target_functions.
    """

    if "int" in type:
        converted_value = web3.toInt(hex_bytes)
    elif "string" in type:
        converted_value = web3.toText(hex_bytes)
    elif "address" in type:
        converted_value = web3.toChecksumAddress(hex_bytes)
    else:
        converted_value = hex_bytes.hex()

    return converted_value
