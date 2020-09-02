#!/usr/bin/env python3

import argparse
import logging
import sys

from crytic_compile import cryticparser

from slither.tools.similarity.info import info
from slither.tools.similarity.test import test
from slither.tools.similarity.train import train
from slither.tools.similarity.plot import plot

logging.basicConfig()
logger = logging.getLogger("Slither-simil")

modes = ["info", "test", "train", "plot"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Code similarity detection tool. For usage, see https://github.com/crytic/slither/wiki/Code-Similarity-detector"
    )

    parser.add_argument("mode", help="|".join(modes))

    parser.add_argument("model", help="model.bin")

    parser.add_argument(
        "--filename", action="store", dest="filename", help="contract.sol"
    )

    parser.add_argument("--fname", action="store", dest="fname", help="Target function")

    parser.add_argument(
        "--ext", action="store", dest="ext", help="Extension to filter contracts"
    )

    parser.add_argument(
        "--nsamples",
        action="store",
        type=int,
        dest="nsamples",
        help="Number of contract samples used for training",
    )

    parser.add_argument(
        "--ntop",
        action="store",
        type=int,
        dest="ntop",
        default=10,
        help="Number of more similar contracts to show for testing",
    )

    parser.add_argument(
        "--input", action="store", dest="input", help="File or directory used as input"
    )

    parser.add_argument(
        "--version",
        help="displays the current version",
        version="0.0",
        action="version",
    )

    cryticparser.init(parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    return args


# endregion
###################################################################################
###################################################################################
# region Main
###################################################################################
###################################################################################


def main():
    args = parse_args()

    default_log = logging.INFO
    logger.setLevel(default_log)

    mode = args.mode

    if mode == "info":
        info(args)
    elif mode == "train":
        train(args)
    elif mode == "test":
        test(args)
    elif mode == "plot":
        plot(args)
    else:
        to_log = "Invalid mode!. It should be one of these: %s" % ", ".join(modes)
        logger.error(to_log)
        sys.exit(-1)


if __name__ == "__main__":
    main()

# endregion
