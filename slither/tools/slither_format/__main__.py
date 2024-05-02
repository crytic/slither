import logging
from typing import Annotated

import typer


from slither import Slither
from slither.tools.slither_format.slither_format import slither_format


from slither.__main__ import app
from slither.utils.command_line import target_type, SlitherState, SlitherApp, GroupWithCrytic

format_app: SlitherApp = SlitherApp()
app.add_typer(format_app, name="format")


logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

# Slither detectors for which slither-format currently works
available_detectors = [
    "unused-state",
    "solc-version",
    "pragma",
    "naming-convention",
    "external-function",
    "constable-states",
    "constant-function-asm",
    "constant-function-state",
]


@format_app.callback(cls=GroupWithCrytic)
def main(
    ctx: typer.Context,
    target: target_type,
    verbose_test: Annotated[
        bool, typer.Option("--verbose-test", "-v", help="Verbose mode output for testing")
    ] = False,  # Unused?
    verbose_json: Annotated[
        bool, typer.Option("--verbose-json", "-j", help="Verbose mode output for testing")
    ] = False,  # Unused?
    detectors_to_run: Annotated[
        str,
        typer.Option(
            "--detect",
            help=f"Comma-separated list of detectors. Available detectors: {', '.join(available_detectors)}",
            rich_help_panel="Detectors",
        ),
    ] = "all",
    detectors_to_exclude: Annotated[
        str,
        typer.Option(
            "--exclude",
            help="Comma-separated list of detectors that should be excluded or all.",
            rich_help_panel="Detectors",
        ),
    ] = "",
) -> None:
    # ------------------------------
    #       Usage: python3 -m slither_format filename
    #       Example: python3 -m slither_format contract.sol
    # ------------------------------

    # Perform slither analysis on the given filename
    state = ctx.ensure_object(SlitherState)
    slither = Slither(target.target, **state)

    # Format the input files based on slither analysis
    state.update(
        {
            "detectors_to_run": detectors_to_run,
            "detectors_to_exclude": detectors_to_exclude,
        }
    )
    slither_format(slither, **state)


if __name__ == "__main__":
    format_app()
