import logging
import sys

import typer

from slither.tools.doctor.utils import report_section
from slither.tools.doctor.checks import ALL_CHECKS

from slither.__main__ import app
from slither.utils.command_line import target_type, SlitherState, SlitherApp, GroupWithCrytic

doctor: SlitherApp = SlitherApp()
app.add_typer(doctor, name="doctor")


@doctor.callback(cls=GroupWithCrytic)
def main(
    ctx: typer.Context,
    project: target_type,
) -> None:
    """Troubleshoot running Slither on your project."""
    # log on stdout to keep output in order
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, force=True)

    state = ctx.ensure_object(SlitherState)

    for check in ALL_CHECKS:
        with report_section(check.title):
            check.function(project=project.target, **state)


if __name__ == "__main__":
    doctor()
