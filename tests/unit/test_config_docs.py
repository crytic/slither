import subprocess
import sys


def test_usage_config_options_are_generated() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/generate_config_docs.py", "--check"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
