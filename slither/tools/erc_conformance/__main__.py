import argparse
import logging
from collections import defaultdict
from typing import Any, Dict, List, Callable

from crytic_compile import cryticparser

from slither import Slither
from slither.core.declarations import Contract
from slither.utils.erc import ERCS
from slither.utils.output import output_to_json
from .erc.erc1155 import check_erc1155
from .erc.erc20 import check_erc20
from .erc.ercs import generic_erc_checks

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


def parse_args() -> argparse.Namespace:
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(
        description="Check the ERC 20 conformance",
        usage="slither-check-erc project contractName",
    )

    parser.add_argument("project", help="The codebase to be tested.")

    parser.add_argument(
        "contract_name",
        help="The name of the contract. Specify the first case contract that follow the standard. Derived contracts will be checked.",
    )

    parser.add_argument(
        "--erc",
        help=f"ERC to be tested, available {','.join(ERCS.keys())} (default ERC20)",
        action="store",
        default="erc20",
    )

    parser.add_argument(
        "--json",
        help='Export the results as a JSON file ("--json -" to export to stdout)',
        action="store",
        default=False,
    )

    # Add default arguments from crytic-compile
    cryticparser.init(parser)

    return parser.parse_args()


def _log_error(err: Any, args: argparse.Namespace) -> None:
    if args.json:
        output_to_json(args.json, str(err), {"upgradeability-check": []})

    logger.error(err)


def main() -> None:
    args = parse_args()

    # Perform slither analysis on the given filename
    slither = Slither(args.project, **vars(args))

    ret: Dict[str, List] = defaultdict(list)

    if args.erc.upper() in ERCS:

        contracts = slither.get_contract_from_name(args.contract_name)

        if len(contracts) != 1:
            err = f"Contract not found: {args.contract_name}"
            _log_error(err, args)
            return
        contract = contracts[0]
        # First elem is the function, second is the event
        erc = ERCS[args.erc.upper()]
        generic_erc_checks(contract, erc[0], erc[1], ret)

        if args.erc.upper() in ADDITIONAL_CHECKS:
            ADDITIONAL_CHECKS[args.erc.upper()](contract, ret)

    else:
        err = f"Incorrect ERC selected {args.erc}"
        _log_error(err, args)
        return

    if args.json:
        output_to_json(args.json, None, {"upgradeability-check": ret})


if __name__ == "__main__":
    main()
