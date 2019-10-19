import argparse
import logging
from slither import Slither
from crytic_compile import cryticparser
from slither.utils.erc import ERCS
from .erc.ercs import generic_erc_checks

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

logger = logging.getLogger("Slither-conformance")
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
logger.addHandler(ch)
logger.handlers[0].setFormatter(formatter)
logger.propagate = False



def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(description='Check the ERC 20 conformance',
                                     usage='slither-erc project contractName')

    parser.add_argument('project',
                        help='The codebase to be tested.')

    parser.add_argument('contract_name',
                        help='The name of the contract. Specify the first case contract that follow the standard. Derived contracts will be checked.')

    parser.add_argument(
        "--erc",
        help=f"ERC to be tested, available {','.join(ERCS.keys())} (default ERC20)",
        action="store",
        default="erc20",
    )

    # Add default arguments from crytic-compile
    cryticparser.init(parser)

    return parser.parse_args()

def main():
    args = parse_args()

    # Perform slither analysis on the given filename
    slither = Slither(args.project, **vars(args))

    if args.erc.upper() in ERCS:

        contract = slither.get_contract_from_name(args.contract_name)

        if not contract:
            logger.error(f'Contract not found: {args.contract_name}')
            return
        # First elem is the function, second is the event
        erc = ERCS[args.erc.upper()]
        generic_erc_checks(contract, erc[0], erc[1])
    else:
        logger.error(f'Incorrect ERC selected {args.erc}')
        return


if __name__ == '__main__':
    main()
