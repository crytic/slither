import logging
from pathlib import Path
from typing import Annotated

import typer

# Configure logging before slither imports to suppress CryticCompile INFO messages
logging.basicConfig()
logging.getLogger("CryticCompile").setLevel(logging.WARNING)
logger = logging.getLogger("Slither-Interface")
logger.setLevel(logging.INFO)

from slither import Slither
from slither.utils.code_generation import generate_interface

from slither.__main__ import app
from slither.utils.command_line import target_type, SlitherState, SlitherApp, GroupWithCrytic

interface_cmd: SlitherApp = SlitherApp()
app.add_typer(interface_cmd, name="interface")


@interface_cmd.callback(cls=GroupWithCrytic)
def main_callback(
    ctx: typer.Context,
    contract_name: Annotated[
        str, typer.Argument(help="The name of the contract (case sensitive).")
    ],
    target: target_type,
    unroll_structs: Annotated[
        bool,
        typer.Option(
            help="Whether to use structures' underlying types instead of the user-defined type."
        ),
    ] = False,
    exclude_events: Annotated[
        bool, typer.Option(help="Excludes event signatures in the interface.")
    ] = False,
    exclude_errors: Annotated[
        bool, typer.Option(help="Excludes custom errors signatures in the interface.")
    ] = False,
    exclude_enums: Annotated[
        bool, typer.Option(help="Excludes enum definitions in the interface.")
    ] = False,
    exclude_structs: Annotated[
        bool, typer.Option(help="Excludes structs definitions in the interface.")
    ] = False,
) -> None:
    """Generates code for a Solidity interface from contract"""

    state = ctx.ensure_object(SlitherState)
    slither = Slither(target.target, **state)

    _contract = slither.get_contract_from_name(contract_name)[0]

    interface = generate_interface(
        contract=_contract,
        unroll_structs=unroll_structs,
        include_events=not exclude_events,
        include_errors=not exclude_errors,
        include_enums=not exclude_enums,
        include_structs=not exclude_structs,
    )

    # add version pragma
    if _contract.compilation_unit.pragma_directives:
        interface = (
            f"pragma solidity {_contract.compilation_unit.pragma_directives[0].version};\n\n"
            + interface
        )

    # write interface to file
    export = Path("crytic-export", "interfaces")
    export.mkdir(parents=True, exist_ok=True)
    filename = f"I{contract_name}.sol"
    path = Path(export, filename)
    logger.info(f" Interface exported to {path}")
    with open(path, "w", encoding="utf8") as f:
        f.write(interface)

    raise typer.Exit(0)


def main():
    """Entry point for the slither-interface CLI."""
    interface_cmd()


if __name__ == "__main__":
    main()
