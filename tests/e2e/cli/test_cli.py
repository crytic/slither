from typing import Optional, Union, Sequence, IO, Any, Mapping
from typer.testing import CliRunner
from slither.__main__ import app


def test_app():
    runner = CliRunner()

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
