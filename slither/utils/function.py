from Crypto.Hash import keccak


def get_function_id(sig: str) -> int:
    """'
        Return the function id of the given signature
    Args:
        sig (str)
    Return:
        (int)
    """
    hash = keccak.new(digest_bits=256)
    hash.update(sig.encode("utf-8"))
    return int("0x" + hash.hexdigest()[:8], 16)
