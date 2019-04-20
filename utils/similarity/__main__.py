#!/usr/bin/env python3

import argparse
import logging
import sys
import traceback
import operator

from .info     import info
from .test     import test
from .train    import train
from .plot     import plot

logging.basicConfig()
logger = logging.getLogger("Slither-simil")

slither_simil_usage = "USAGE" # TODO 
modes = ["info", "test", "train", "plot"]

def parse_args():
    parser = argparse.ArgumentParser(description='Code similarity detection tool',
                                     usage=slither_simil_usage)

    parser.add_argument('mode',
                        help="|".join(modes))

    parser.add_argument('model',
                        help='model.bin')

    parser.add_argument('--solc',
                        help='solc path',
                        action='store',
                        default='solc')

    parser.add_argument('--filename',
                        action='store',
                        dest='filename',
                        help='contract.sol')

    parser.add_argument('--contract',
                        action='store',
                        dest='contract',
                        help='Contract')

    parser.add_argument('--filter',
                        action='store',
                        dest='filter',
                        help='Extension to filter contracts')

    parser.add_argument('--fname',
                        action='store',
                        dest='fname',
                        help='Function name')

    parser.add_argument('--nsamples',
                        action='store',
                        type=int,
                        dest='nsamples',
                        help='Number of contract samples used for training')

    parser.add_argument('--ntop',
                        action='store',
                        type=int,
                        dest='ntop',
                        default=10,
                        help='Number of more similar contracts to show for testing')

    parser.add_argument('--input',
                        action='store',
                        dest='input',
                        help='File or directory used as input')

    parser.add_argument('--version',
                        help='displays the current version',
                        version="0.0",
                        action='version')

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
    
    try:
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
            logger.error('Invalid mode!. It should be one of these: %s' % ", ".join(modes))
            sys.exit(-1)

    except Exception:
        logger.error('Error in %s' % args.filename)
        logger.error(traceback.format_exc())
        sys.exit(-1)

if __name__ == '__main__':
    main()

# endregion
