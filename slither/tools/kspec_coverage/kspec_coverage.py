from pathlib import Path
from typing import Union

import typer

from slither.tools.kspec_coverage.analysis import run_analysis
from slither import Slither
from slither.utils.command_line import SlitherState


def kspec_coverage(
    contract: str, kspec: str, ctx: typer.Context, output_json: Union[bool, Path] = False
) -> None:

    state = ctx.ensure_object(SlitherState)
    slither = Slither(contract, **state)

    compilation_units = slither.compilation_units
    if len(compilation_units) != 1:
        print("Only single compilation unit supported")
        return
    # Run the analysis on the Klab specs
    run_analysis(compilation_units[0], kspec, output_json)
