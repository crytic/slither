from Crypto.Hash import keccak


def get_function_id(sig: str) -> int:
    """'
        Return the function id of the given signature
    Args:
        sig (str)
    Return:
        (int)
    """
    digest = keccak.new(digest_bits=256)
    digest.update(sig.encode("utf-8"))
    return int("0x" + digest.hexdigest()[:8], 16)
