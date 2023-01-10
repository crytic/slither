import argparse
import logging
import os
from pathlib import Path

from crytic_compile import cryticparser

from slither import Slither
from slither.tools.slither_log.slither_log import SlitherLog

logging.basicConfig()
logger = logging.getLogger("Slither-Log")
logger.setLevel(logging.INFO)


def parse_args() -> argparse.Namespace:
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(
        description="Adds console.log to all functions for hardhat debugging",
        usage=(
            "\nTo generate a git patch for a solidity file:\n"
            + "\tslither-log $TARGET\n"
            + "To apply a patch (from same directory slither-log was called in):\n"
            + "\tgit apply --whitespace=fix crytic-export/slither-log/$PATCHFILE\n"
            + "To remove a patch:\n"
            + "\tgit apply -R crytic-export/slither-log/$PATCHFILE\n"
            + "It's recommended to remove a patch before making edits, otherwise the patch will no longer be valid for removal.\n"
            + "If patch no longer applies, remove portions from the edited file from the patch file and it will still work on un-edited files\n"
            + "slither-log --help for more options"
        ),
    )

    parser.add_argument("filename", help="The filename of the contract to analyze.")

    group_patching = parser.add_argument_group("Patching options")

    group_patching.add_argument(
        "--force-patch",
        help="Automatically apply the generated patch",
        default=False,
        action="store_true",
    )

    group_patching.add_argument(
        "--allow-bytes-conversion",
        help=(
            "Hardhat console can't easily print bytes. \n"
            + "This will cast any static bytes arrays to bytes32, then to uint256 to allow for easier logging.\n"
            + "User can convert back to the appropriate bytes size manually if desired.\n"
            + "Default behavior is to not log any bytes. This option does not affect dynamic bytes arrays."
        ),
        default=False,
        action="store_true",
    )

    group_patching.add_argument(
        "--whitelist-function",
        help="Edit only specified function(s). Call several times to add more than one function. Use canonical name - Contract.functionName(paramTypes)",
        default=[],
        action="append",
    )

    group_patching.add_argument(
        "--blacklist-function",
        help="Exclude function(s) from editing. Call several times to add more than one function. Use canonical name - Contract.functionName(paramTypes)",
        default=[],
        action="append",
    )

    group_patching.add_argument(
        "--whitelist-contract",
        help="Edit only specified contract(s). Call several times to add more than one contract",
        default=[],
        action="append",
    )

    group_patching.add_argument(
        "--blacklist-contract",
        help="Exclude contract(s) from editing. Call several times to add more than one contract",
        default=[],
        action="append",
    )

    # Add default arguments from crytic-compile
    cryticparser.init(parser)

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    slither_log = SlitherLog(
        Slither(args.filename, **vars(args)),
        args.allow_bytes_conversion,
        whitelisted_functions=args.whitelist_function,
        blacklisted_functions=args.blacklist_function,
        whitelisted_contracts=args.whitelist_contract,
        blacklisted_contracts=args.blacklist_contract,
    )
    slither_log.add_console_log()

    # write patch to file
    export = Path("crytic-export", "slither-log")
    export.mkdir(parents=True, exist_ok=True)
    filename = f"{args.filename[:-4]}.slither-log.patch"
    path = Path(export, filename)
    logger.info(f"Export {filename}")
    with open(path, "w", encoding="utf8") as f:
        f.write(slither_log.diffs)

    if args.force_patch:
        os.system(f"git apply --whitespace=fix {export}/{filename}")


if __name__ == "__main__":
    main()
