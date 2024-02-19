import argparse
import logging
import sys

from crytic_compile import cryticparser

from slither import Slither
from slither.tools.flat.flattening import (
    Flattening,
    Strategy,
    STRATEGIES_NAMES,
    DEFAULT_EXPORT_PATH,
)

logging.basicConfig()
logger = logging.getLogger("Slither")
logger.setLevel(logging.INFO)


def main() -> None:
    args = parse_args()

    slither = Slither(args.filename, **vars(args))

    for compilation_unit in slither.compilation_units:

        flat = Flattening(
            compilation_unit,
            external_to_public=args.convert_external,
            remove_assert=args.remove_assert,
            convert_library_to_internal=args.convert_library_to_internal,
            private_to_internal=args.convert_private,
            export_path=args.dir,
            pragma_solidity=args.pragma_solidity,
        )

        try:
            strategy = Strategy[args.strategy]
        except KeyError:
            to_log = f"{args.strategy} is not a valid strategy, use: {STRATEGIES_NAMES} (default MostDerived)"
            logger.error(to_log)
            return
        flat.export(
            strategy=strategy,
            target=args.contract,
            json=args.json,
            zip=args.zip,
            zip_type=args.zip_type,
        )


if __name__ == "__main__":
    main()
