import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Callable, Annotated

import typer


from slither import Slither
from slither.core.declarations import Contract
from slither.utils.erc import ERCS
from slither.utils.output import output_to_json, OutputFormat
from .erc.erc1155 import check_erc1155
from .erc.erc20 import check_erc20
from .erc.ercs import generic_erc_checks

from slither.__main__ import app
from slither.utils.command_line import target_type, SlitherState, SlitherApp, GroupWithCrytic

conformance: SlitherApp = SlitherApp()
app.add_typer(conformance, name="check-erc")


logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

logger = logging.getLogger("Slither-conformance")
logger.setLevel(logging.INFO)


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
            return
        contract = contracts[0]
        # First elem is the function, second is the event
        erc = ERCS[erc_arg.upper()]
        generic_erc_checks(contract, erc[0], erc[1], ret)

        if erc_arg.upper() in ADDITIONAL_CHECKS:
            ADDITIONAL_CHECKS[erc_arg.upper()](contract, ret)

    else:
        err = f"Incorrect ERC selected {erc_arg}"
        _log_error(err, output_format=output_format, output_file=output_file)
        return

    if output_format == OutputFormat.JSON:
        output_to_json(output_file.as_posix(), None, {"erc-conformance-check": ret})


def main():
    """Entry point for the slither-check-erc CLI."""
    conformance()


if __name__ == "__main__":
    main()
