from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slither.core.declarations.contract import Contract

_TESTS_PATTERNS = ["Test", "test", "Mock", "mock"]
TESTS_PATTERNS = _TESTS_PATTERNS + [x + "s" for x in _TESTS_PATTERNS]


def _is_test_pattern(txt: str, pattern: str) -> bool:
    """
    Check if the txt starts with the pattern, or ends with it
    :param pattern:
    :return:
    """
    if txt.endswith(pattern):
        return True
    if not txt.startswith(pattern):
        return False
    length = len(pattern)
    if len(txt) <= length:
        return True
    return txt[length] == "_" or txt[length].isupper()


def is_test_file(path: Path) -> bool:
    """
    Check if the given path points to a test/mock file
    :param path:
    :return:
    """
    return any((test_pattern in path.parts for test_pattern in TESTS_PATTERNS))


def is_test_contract(contract: "Contract") -> bool:
    """
    Check if the contract is a test/mock
    :param contract:
    :return:
    """
    return (
        _is_test_pattern(contract.name, "Test")
        or _is_test_pattern(contract.name, "Mock")
        or (
            contract.source_mapping["filename_absolute"]
            and is_test_file(Path(contract.source_mapping["filename_absolute"]))
        )
    )
