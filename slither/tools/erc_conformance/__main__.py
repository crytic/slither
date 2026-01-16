import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Callable, Annotated

import typer

# Configure logging before slither imports to suppress CryticCompile INFO messages
logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)
logging.getLogger("CryticCompile").setLevel(logging.WARNING)

logger = logging.getLogger("Slither-conformance")
logger.setLevel(logging.INFO)

from slither import Slither  # noqa: E402
from slither.core.declarations import Contract  # noqa: E402
from slither.utils.erc import ERCS  # noqa: E402
from slither.utils.output import output_to_json, OutputFormat  # noqa: E402
from .erc.erc1155 import check_erc1155  # noqa: E402
from .erc.erc20 import check_erc20  # noqa: E402
from .erc.ercs import generic_erc_checks  # noqa: E402

from slither.__main__ import app  # noqa: E402
from slither.utils.command_line import target_type, SlitherState, SlitherApp, GroupWithCrytic  # noqa: E402

conformance: SlitherApp = SlitherApp()
app.add_typer(conformance, name="check-erc")


ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s")
logger.addHandler(ch)
logger.handlers[0].setFormatter(formatter)
logger.propagate = False

ADDITIONAL_CHECKS: Dict[str, Callable[[Contract, Dict[str, List]], Dict[str, List]]] = {
    "ERC20": check_erc20,
    "ERC1155": check_erc1155,
}


def _log_error(err: Any, output_format: OutputFormat, output_file: Path) -> None:
    if output_format == OutputFormat.JSON:
        output_to_json(output_file.as_posix(), str(err), {"erc-conformance-check": []})

    logger.error(err)


@conformance.callback(cls=GroupWithCrytic)
def main_callback(
    ctx: typer.Context,
    target: target_type,
    contract_name: Annotated[
        str,
        typer.Argument(
            help="The name of the contract. Specify the first case contract that follow the "
            "standard. Derived contracts will be checked."
        ),
    ],
    erc_arg: Annotated[
        str, typer.Option("--erc", help=f"ERC to be tested, available {','.join(ERCS.keys())}.")
    ] = "erc20",
) -> None:
    """Check the conformance with a specified ERC."""
    state = ctx.ensure_object(SlitherState)

    # Perform slither analysis on the given filename
    slither = Slither(target.target, **state)

    ret: Dict[str, List] = defaultdict(list)
    output_format = state.get("output_format", OutputFormat.TEXT)
    output_file = state.get("output_file", Path("-"))

    if erc_arg.upper() in ERCS:
        contracts = slither.get_contract_from_name(contract_name)

        if len(contracts) != 1:
            err = f"Contract not found: {contract_name}"
            _log_error(err, output_format=output_format, output_file=output_file)
            raise typer.Exit(1)
        contract = contracts[0]
        # First elem is the function, second is the event
        erc = ERCS[erc_arg.upper()]
        generic_erc_checks(contract, erc[0], erc[1], ret)

        if erc_arg.upper() in ADDITIONAL_CHECKS:
            ADDITIONAL_CHECKS[erc_arg.upper()](contract, ret)

    else:
        err = f"Incorrect ERC selected {erc_arg}"
        _log_error(err, output_format=output_format, output_file=output_file)
        raise typer.Exit(1)

    if output_format == OutputFormat.JSON:
        output_to_json(output_file.as_posix(), None, {"erc-conformance-check": ret})

    raise typer.Exit(0)


def main():
    """Entry point for the slither-check-erc CLI."""
    conformance()


if __name__ == "__main__":
    main()
