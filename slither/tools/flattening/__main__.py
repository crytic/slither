import argparse
import logging
from slither import Slither
from crytic_compile import cryticparser
from .flattening import Flattening

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)
logger = logging.getLogger("Slither-flattening")
logger.setLevel(logging.INFO)

def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(description='Contracts flattening',
                                     usage='slither-flat filename')

    parser.add_argument('filename',
                        help='The filename of the contract or project to analyze.')

    parser.add_argument('--convert-external',
                        help='Convert external to public.',
                        action='store_true')

    parser.add_argument('--remove-assert',
                        help='Remove call to assert().',
                        action='store_true')

    parser.add_argument('--contract',
                        help='Flatten a specific contract (default: all most derived contracts).',
                        default=None)

    # Add default arguments from crytic-compile
    cryticparser.init(parser)

    return parser.parse_args()


def main():
    args = parse_args()

    slither = Slither(args.filename, **vars(args))
    flat = Flattening(slither, external_to_public=args.convert_external, remove_assert=args.remove_assert)

    flat.export(target=args.contract)


if __name__ == '__main__':
    main()
