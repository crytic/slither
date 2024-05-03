import logging
from typing import Annotated

from slither.tools.kspec_coverage.kspec_coverage import kspec_coverage

import typer

from slither.__main__ import app
from slither.utils.command_line import target_type, SlitherApp, GroupWithCrytic, SlitherState
from slither.utils.output import OutputFormat

kspec_coverage_app: SlitherApp = SlitherApp()
app.add_typer(kspec_coverage_app, name="check-kspec")

logging.basicConfig()
logger = logging.getLogger("Slither.kspec")
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s")
logger.addHandler(ch)
logger.handlers[0].setFormatter(formatter)
logger.propagate = False


@kspec_coverage_app.callback(cls=GroupWithCrytic)
def main(
    ctx: typer.Context,
    target: target_type,
    kspec: Annotated[
        str,
        typer.Argument(help="The filename of the Klab spec markdown for the analyzed contract(s)"),
    ],
) -> None:
    """Kspec coverage."""
    state = ctx.ensure_object(SlitherState)
    output_json = False
    if state.get("output_format") == OutputFormat.JSON:
        output_json = state.get("output_file")

    kspec_coverage(
        target,
        kspec,
        ctx,
        output_json,
    )


if __name__ == "__main__":
    kspec_coverage_app()
