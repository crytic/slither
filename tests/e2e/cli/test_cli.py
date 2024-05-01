from typing import Optional, Union, Sequence, IO, Any, Mapping

import typer
from click.testing import Result
from typer.testing import CliRunner


from slither.__main__ import app


# class TyperRunner(CliRunner):
#     def __init__(self, typer_app: typer.Typer, *args, **kwargs):
#         self.app = typer_app
#         super().__init__(*args, **kwargs)
#
#     def invoke(  # type: ignore
#         self,
#         *args,
#         **kwargs: Any,
#     ):
#         super().invoke(*args, **kwargs)


def test_app():
    runner = CliRunner()

    result = runner.invoke(app, ["detect", ".", "--detect", "all"], prog_name="slither")
    print(result.stdout)
    assert result.exit_code == 0


def test_direct():
    import sys

    sys.argv = ["slither", "detect", "."]
    app()
