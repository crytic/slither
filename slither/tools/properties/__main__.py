import argparse
import logging
import sys

from crytic_compile import cryticparser

from slither import Slither
from slither.tools.properties.properties.erc20 import generate_erc20, ERC20_PROPERTIES
from slither.tools.properties.addresses.address import (
    Addresses,
    OWNER_ADDRESS,
    USER_ADDRESS,
    ATTACKER_ADDRESS,
)
from slither.utils.myprettytable import MyPrettyTable

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

logger = logging.getLogger("Slither")
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s")
logger.addHandler(ch)
logger.handlers[0].setFormatter(formatter)
logger.propagate = False


def _all_scenarios():
    txt = "\n"
    txt += "#################### ERC20 ####################\n"
    for k, value in ERC20_PROPERTIES.items():
        txt += f"{k} - {value.description}\n"

    return txt


def _all_properties():
    table = MyPrettyTable(["Num", "Description", "Scenario"])
    idx = 0
    for scenario, value in ERC20_PROPERTIES.items():
        for prop in value.properties:
            table.add_row([idx, prop.description, scenario])
            idx = idx + 1
    return table


class ListScenarios(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, *args, **kwargs):  # pylint: disable=signature-differs
        logger.info(_all_scenarios())
        parser.exit()


class ListProperties(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, *args, **kwargs):  # pylint: disable=signature-differs
        logger.info(_all_properties())
        parser.exit()


def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(
        description="Demo",
        usage="slither-demo filename",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "filename", help="The filename of the contract or truffle directory to analyze."
    )

    parser.add_argument("--contract", help="The targeted contract.")

    parser.add_argument(
        "--scenario",
        help="Test a specific scenario. Use --list-scenarios to see the available scenarios. Default Transferable",
        default="Transferable",
    )

    parser.add_argument(
        "--list-scenarios",
        help="List available scenarios",
        action=ListScenarios,
        nargs=0,
        default=False,
    )

    parser.add_argument(
        "--list-properties",
        help="List available properties",
        action=ListProperties,
        nargs=0,
        default=False,
    )

    parser.add_argument(
        "--address-owner", help=f"Owner address. Default {OWNER_ADDRESS}", default=None
    )

    parser.add_argument(
        "--address-user", help=f"Owner address. Default {USER_ADDRESS}", default=None
    )

    parser.add_argument(
        "--address-attacker",
        help=f"Attacker address. Default {ATTACKER_ADDRESS}",
        default=None,
    )

    # Add default arguments from crytic-compile
    cryticparser.init(parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


def main():
    args = parse_args()

    # Perform slither analysis on the given filename
    slither = Slither(args.filename, **vars(args))

    contract = slither.get_contract_from_name(args.contract)
    if not contract:
        if len(slither.contracts) == 1:
            contract = slither.contracts[0]
        else:
            if args.contract is None:
                to_log = "Specify the target: --contract ContractName"
            else:
                to_log = f"{args.contract} not found"
            logger.error(to_log)
            return

    addresses = Addresses(args.address_owner, args.address_user, args.address_attacker)

    generate_erc20(contract, args.scenario, addresses)


if __name__ == "__main__":
    main()
