import argparse
import inspect
import logging
import sys

from crytic_compile import cryticparser

from slither import Slither
from slither.tools.mutator.mutators import all_mutators
from .mutators.abstract_mutator import AbstractMutator
from .utils.command_line import output_mutators

logging.basicConfig()
logger = logging.getLogger("Slither")
logger.setLevel(logging.INFO)


###################################################################################
###################################################################################
# region Cli Arguments
###################################################################################
###################################################################################


def parse_args():
    parser = argparse.ArgumentParser(
        description="Experimental smart contract mutator. Based on https://arxiv.org/abs/2006.11597",
        usage="slither-mutate target",
    )

    parser.add_argument("codebase", help="Codebase to analyze (.sol file, truffle directory, ...)")

    parser.add_argument(
        "--list-mutators",
        help="List available detectors",
        action=ListMutators,
        nargs=0,
        default=False,
    )

    # Initiate all the crytic config cli options
    cryticparser.init(parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


def _get_mutators():
    detectors = [getattr(all_mutators, name) for name in dir(all_mutators)]
    detectors = [c for c in detectors if inspect.isclass(c) and issubclass(c, AbstractMutator)]
    return detectors


class ListMutators(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, *args, **kwargs):  # pylint: disable=signature-differs
        checks = _get_mutators()
        output_mutators(checks)
        parser.exit()


# endregion
###################################################################################
###################################################################################
# region Main
###################################################################################
###################################################################################


def main():

    args = parse_args()

    print(args.codebase)
    sl = Slither(args.codebase, **vars(args))

    for M in _get_mutators():
        m = M(sl)
        m.mutate()


# endregion
