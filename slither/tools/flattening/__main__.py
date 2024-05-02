import logging
from pathlib import Path
from typing import Annotated, Optional
import typer

from slither import Slither
from slither.tools.flattening.flattening import (
    Flattening,
    Strategy,
    DEFAULT_EXPORT_PATH,
)
from slither.utils.output import OutputFormat
from slither.__main__ import app
from slither.utils.command_line import target_type, SlitherState, SlitherApp, GroupWithCrytic

flattener: SlitherApp = SlitherApp()
app.add_typer(flattener, name="flattener")

logging.basicConfig()
logger = logging.getLogger("Slither")
logger.setLevel(logging.INFO)


@flattener.callback(cls=GroupWithCrytic)
def main(
    ctx: typer.Context,
    target: target_type,
    contract: Annotated[Optional[str], typer.Option(help="Flatten one contract.")] = None,
    strategy: Annotated[
        Strategy,
        typer.Option(help="Flattening strategy."),
    ] = Strategy.MostDerived,
    dir_: Annotated[Path, typer.Option(help="Export directory.")] = DEFAULT_EXPORT_PATH,
    convert_external: Annotated[bool, typer.Option(help="Convert external to public.")] = False,
    convert_private: Annotated[
        bool, typer.Option(help="Convert private variables to internal.")
    ] = False,
    convert_library_to_internal: Annotated[
        bool,
        typer.Option(help="Convert external or public functions to internal in library."),
    ] = False,
    remove_assert: Annotated[bool, typer.Option(help="Remove call to assert().")] = False,
    pragma_solidity: Annotated[
        Optional[str], typer.Option(help="Set the solidity pragma with a given version.")
    ] = None,
) -> None:
    """Flatten a contract using the specified strategy."""
    state = ctx.ensure_object(SlitherState)
    slither = Slither(target.target, **state)

    for compilation_unit in slither.compilation_units:

        flat = Flattening(
            compilation_unit,
            external_to_public=convert_external,
            remove_assert=remove_assert,
            convert_library_to_internal=convert_library_to_internal,
            private_to_internal=convert_private,
            export_path=dir_.as_posix(),
            pragma_solidity=pragma_solidity,
        )

        json = None
        zip_ = None
        zip_type = None

        if state.get("output_format") == OutputFormat.JSON:
            json = state.get("output_file", Path("-")).as_posix()
        elif state.get("output_format") == OutputFormat.ZIP:
            zip_ = state.get("output_file", Path("-")).as_posix()
            zip_type = state.get("zip_type", [])

        flat.export(
            strategy=strategy,
            target=contract,
            json=json,
            zip=zip_,
            zip_type=zip_type,
        )


if __name__ == "__main__":
    flattener()
