from pathlib import Path

import pytest

from slither import Slither
from slither.exceptions import SlitherException


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data" / "ignore_comments"


def test_end_without_start_raises(solc_binary_path) -> None:
    """Malformed slither-disable-end without matching start should raise SlitherException."""
    solc_path = solc_binary_path("0.8.15")
    with pytest.raises(SlitherException) as exc_info:
        Slither(Path(TEST_DATA_DIR, "end_without_start.sol").as_posix(), solc=solc_path)
    assert "slither-disable-end without slither-disable-start" in str(exc_info.value)


def test_consecutive_starts_raises(solc_binary_path) -> None:
    """Consecutive slither-disable-start without end should raise SlitherException."""
    solc_path = solc_binary_path("0.8.15")
    with pytest.raises(SlitherException) as exc_info:
        Slither(Path(TEST_DATA_DIR, "consecutive_starts.sol").as_posix(), solc=solc_path)
    assert "Consecutive slither-disable-starts without slither-disable-end" in str(exc_info.value)
