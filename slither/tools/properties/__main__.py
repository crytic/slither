import logging
from typing import Annotated
import typer

from slither import Slither
from slither.tools.properties.properties.erc20 import generate_erc20, ERC20_PROPERTIES
from slither.tools.properties.addresses.address import (
    Addresses,
    OWNER_ADDRESS,
    USER_ADDRESS,
    ATTACKER_ADDRESS,
)
from slither.utils.myprettytable import MyPrettyTable

from slither.__main__ import app
from slither.utils.command_line import target_type, SlitherState, SlitherApp, GroupWithCrytic


properties_app: SlitherApp = SlitherApp()
app.add_typer(properties_app, name="prop")


logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

logger = logging.getLogger("Slither")
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s")
logger.addHandler(ch)
logger.handlers[0].setFormatter(formatter)
logger.propagate = False


def _all_scenarios() -> str:
    txt = "\n"
    txt += "#################### ERC20 ####################\n"
    for k, value in ERC20_PROPERTIES.items():
        txt += f"{k} - {value.description}\n"

    return txt


def _all_properties() -> MyPrettyTable:
    table = MyPrettyTable(["Num", "Description", "Scenario"])
    idx = 0
    for scenario, value in ERC20_PROPERTIES.items():
        for prop in value.properties:
            table.add_row([str(idx), prop.description, scenario])
            idx = idx + 1
    return table


def list_scenarios_action(ctx: typer.Context, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return

    logger.info(_all_scenarios())
    raise typer.Exit()


def list_properties_action(ctx: typer.Context, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return

    logger.info(_all_properties())
    raise typer.Exit()


@properties_app.callback(cls=GroupWithCrytic)
def main_callback(
    ctx: typer.Context,
    target: target_type,
    contract: Annotated[str, typer.Option(help="The targeted contract.")],
    scenario: Annotated[
        str,
        typer.Option(
            help="Test a specific scenario. Use --list-scenarios to see the available scenarios."
        ),
    ] = "Transferable",
    list_scenarios: Annotated[
        bool,
        typer.Option(
            "--list-scenarios",
            help="List available scenarios",
            callback=list_scenarios_action,
            is_eager=True,
        ),
    ] = False,
    list_properties: Annotated[
        bool,
        typer.Option(
            "--list-properties",
            help="List available properties",
            callback=list_properties_action,
            is_eager=True,
        ),
    ] = False,
    address_owner: Annotated[
        str, typer.Option("--address-owner", help="Owner address.")
    ] = OWNER_ADDRESS,
    address_user: Annotated[
        str, typer.Option("--address-user", help="User address.")
    ] = USER_ADDRESS,
    address_attacker: Annotated[
        str, typer.Option("--address-attacker", help="Attacker address.")
    ] = ATTACKER_ADDRESS,
) -> None:
    """Generates code properties (e.g., invariants) that can be tested with unit tests or Echidna,
    entirely automatically."""

    # Perform slither analysis on the given filename
    state = ctx.ensure_object(SlitherState)
    slither = Slither(target.target, **state)

    contracts = slither.get_contract_from_name(contract)
    if len(contracts) != 1:
        if len(slither.contracts) == 1:
            contract = slither.contracts[0]
        else:
            if contract is None:
                to_log = "Specify the target: --contract ContractName"
            else:
                to_log = f"{contract} not found"
            logger.error(to_log)
            raise typer.Exit(1)
    else:
        contract = contracts[0]

    addresses = Addresses(address_owner, address_user, address_attacker)

    generate_erc20(contract, scenario, addresses)


def main():
    """Entry point for the slither-prop CLI."""
    properties_app()


if __name__ == "__main__":
    main()
