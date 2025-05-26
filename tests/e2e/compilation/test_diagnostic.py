from pathlib import Path
import shutil
import re

import pytest

from slither import Slither
from slither.exceptions import SlitherException


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"

foundry_available = shutil.which("forge") is not None
project_ready = Path(TEST_DATA_DIR, "test_change/lib/forge-std").exists()


@pytest.mark.skipif(
    not foundry_available or not project_ready, reason="requires Foundry and project setup"
)
def test_diagnostic():

    test_file_directory = TEST_DATA_DIR / "test_change"

    sl = Slither(test_file_directory.as_posix())
    assert len(sl.compilation_units) == 1

    counter_file = test_file_directory / "src" / "Counter.sol"
    shutil.copy(counter_file, counter_file.with_suffix(".bak"))

    with counter_file.open("r") as file:
        content = file.read()

    with counter_file.open("w") as file:
        file.write(re.sub(r"//START.*?//END\n?", "", content, flags=re.DOTALL))

    with pytest.raises(SlitherException):
        Slither(test_file_directory.as_posix(), ignore_compile=True)

    # Restore the original counter so the test is idempotent
    Path(counter_file.with_suffix(".bak")).rename(counter_file)
