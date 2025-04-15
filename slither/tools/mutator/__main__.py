import argparse
import inspect
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Type, List, Any, Optional, Union
from crytic_compile import cryticparser
from slither import Slither
from slither.tools.mutator.utils.testing_generated_mutant import run_test_cmd
from slither.tools.mutator.mutators import all_mutators
from slither.utils.colors import blue, green, magenta, red
from .mutators.abstract_mutator import AbstractMutator
from .utils.command_line import output_mutators
from .utils.file_handling import (
    transfer_and_delete,
    backup_source_file,
    get_sol_file_list,
)

logging.basicConfig()
logger = logging.getLogger("Slither-Mutate")
logger.setLevel(logging.INFO)

###################################################################################
###################################################################################
# region Cli Arguments
###################################################################################
###################################################################################


def parse_args() -> argparse.Namespace:
    """
    Parse the underlying arguments for the program.
    Returns: The arguments for the program.
    """
    parser = argparse.ArgumentParser(
        description="Experimental smart contract mutator. Based on https://arxiv.org/abs/2006.11597",
        usage="slither-mutate <codebase> --test-cmd <test command> <options>",
    )

    parser.add_argument("codebase", help="Codebase to analyze (.sol file, project directory, ...)")

    parser.add_argument(
        "--list-mutators",
        help="List available detectors",
        action=ListMutators,
        nargs=0,
        default=False,
    )

    # argument to add the test command
    parser.add_argument("--test-cmd", help="Command to run the tests for your project")

    # argument to add the test directory - containing all the tests
    parser.add_argument("--test-dir", help="Tests directory")

    # argument to ignore the interfaces, libraries
    parser.add_argument("--ignore-dirs", help="Directories to ignore")

    # time out argument
    parser.add_argument("--timeout", help="Set timeout for test command (by default 30 seconds)")

    # output directory argument
    parser.add_argument(
        "--output-dir", help="Name of output directory (by default 'mutation_campaign')"
    )

    # to print just all the mutants
    parser.add_argument(
        "-v",
        "--verbose",
        help="log mutants that are caught, uncaught, and fail to compile",
        action="store_true",
        default=False,
    )

    # select list of mutators to run
    parser.add_argument(
        "--mutators-to-run",
        help="mutant generators to run",
    )

    # list of contract names you want to mutate
    parser.add_argument(
        "--contract-names",
        help="list of contract names you want to mutate",
    )

    # flag to run full mutation based revert mutator output
    parser.add_argument(
        "--comprehensive",
        help="continue testing minor mutations if severe mutants are uncaught",
        action="store_true",
        default=False,
    )

    # Initiate all the crytic config cli options
    cryticparser.init(parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


def _get_mutators(mutators_list: Union[List[str], None]) -> List[Type[AbstractMutator]]:
    detectors_ = [getattr(all_mutators, name) for name in dir(all_mutators)]
    if mutators_list is not None:
        detectors = [
            c
            for c in detectors_
            if inspect.isclass(c)
            and issubclass(c, AbstractMutator)
            and str(c.NAME) in mutators_list
        ]
    else:
        detectors = [c for c in detectors_ if inspect.isclass(c) and issubclass(c, AbstractMutator)]
    return detectors


class ListMutators(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self, parser: Any, *args: Any, **kwargs: Any
    ) -> None:  # pylint: disable=signature-differs
        checks = _get_mutators(None)
        output_mutators(checks)
        parser.exit()


# endregion
###################################################################################
###################################################################################
# region Main
###################################################################################
###################################################################################


def main() -> None:  # pylint: disable=too-many-statements,too-many-branches,too-many-locals
    args = parse_args()

    # arguments
    test_command: str = args.test_cmd
    test_directory: Optional[str] = args.test_dir
    paths_to_ignore: Optional[str] = args.ignore_dirs
    output_dir: Optional[str] = args.output_dir
    timeout: Optional[int] = args.timeout
    solc_remappings: Optional[str] = args.solc_remaps
    verbose: Optional[bool] = args.verbose
    mutators_to_run: Optional[List[str]] = args.mutators_to_run
    comprehensive_flag: Optional[bool] = args.comprehensive

    logger.info(blue(f"Starting mutation campaign in {args.codebase}"))

    if paths_to_ignore:
        paths_to_ignore_list = paths_to_ignore.strip("][").split(",")
    else:
        paths_to_ignore_list = []

    contract_names: List[str] = []
    if args.contract_names:
        contract_names = args.contract_names.split(",")

    # get all the contracts as a list from given codebase
    sol_file_list: List[str] = get_sol_file_list(Path(args.codebase), paths_to_ignore_list)

    if not contract_names:
        logger.info(blue("Preparing to mutate files:\n- " + "\n- ".join(sol_file_list)))
    else:
        logger.info(blue("Preparing to mutate contracts:\n- " + "\n- ".join(contract_names)))

    # folder where backup files and uncaught mutants are saved
    if output_dir is None:
        output_dir = "./mutation_campaign"

    output_folder = Path(output_dir).resolve()
    if output_folder.is_dir():
        shutil.rmtree(output_folder)

    # setting RR mutator as first mutator
    mutators_list = _get_mutators(mutators_to_run)

    # insert RR and CR in front of the list
    CR_RR_list = []
    duplicate_list = mutators_list.copy()
    for M in duplicate_list:
        if M.NAME == "RR":
            mutators_list.remove(M)
            CR_RR_list.insert(0, M)
        elif M.NAME == "CR":
            mutators_list.remove(M)
            CR_RR_list.insert(1, M)
    mutators_list = CR_RR_list + mutators_list

    logger.info(blue("Timing tests.."))

    # run and time tests, abort if they're broken
    start_time = time.time()
    # no timeout or target_file during the first run, but be verbose on failure
    if not run_test_cmd(test_command, None, None, True):
        logger.error(red("Test suite fails with mutations, aborting"))
        return
    elapsed_time = round(time.time() - start_time)

    # set default timeout
    # default to twice as long as it usually takes to run the test suite
    if timeout is None:
        timeout = int(elapsed_time * 2)
    else:
        timeout = int(timeout)
        if timeout < elapsed_time:
            logger.info(
                red(
                    f"Provided timeout {timeout} is too short for tests that run in {elapsed_time} seconds"
                )
            )
            return

    logger.info(
        green(
            f"Test suite passes in {elapsed_time} seconds, commencing mutation campaign with a timeout of {timeout} seconds\n"
        )
    )

    # Keep a list of all already mutated contracts so we don't mutate them twice
    mutated_contracts: List[str] = []

    for filename in sol_file_list:  # pylint: disable=too-many-nested-blocks
        file_name = os.path.split(filename)[1].split(".sol")[0]
        # slither object
        sl = Slither(filename, **vars(args))
        # create a backup files
        files_dict = backup_source_file(sl.source_code, output_folder)
        # total revert/comment/tweak mutants that were generated and compiled
        total_mutant_counts = [0, 0, 0]
        # total uncaught revert/comment/tweak mutants
        uncaught_mutant_counts = [0, 0, 0]
        # lines those need not be mutated (taken from RR and CR)
        dont_mutate_lines = []

        # perform mutations on {target_contract} in file {file_name}
        # setup placeholder val to signal whether we need to skip if no target_contract is found
        skip_flag = "SLITHER_SKIP_MUTATIONS"
        target_contract = skip_flag if contract_names else ""
        try:
            # loop through all contracts in file_name
            for compilation_unit_of_main_file in sl.compilation_units:
                for contract in compilation_unit_of_main_file.contracts:
                    if contract.name in contract_names and contract.name not in mutated_contracts:
                        target_contract = contract
                        break
                    if not contract_names and contract.name.lower() == file_name.lower():
                        target_contract = contract
                        break

                if target_contract == "":
                    logger.info(
                        f"Cannot find contracts in file {filename}, try specifying them with --contract-names"
                    )
                    continue

                if target_contract == skip_flag:
                    continue

                if target_contract.is_interface:
                    logger.debug(f"Skipping mutations on interface {filename}")
                    continue

                # Add our target to the mutation list
                mutated_contracts.append(target_contract.name)
                logger.info(blue(f"Mutating contract {target_contract}"))
                for M in mutators_list:
                    m = M(
                        compilation_unit_of_main_file,
                        int(timeout),
                        test_command,
                        test_directory,
                        target_contract,
                        solc_remappings,
                        verbose,
                        output_folder,
                        dont_mutate_lines,
                    )
                    (total_counts, uncaught_counts, lines_list) = m.mutate()

                    if m.NAME == "RR":
                        total_mutant_counts[0] += total_counts[0]
                        uncaught_mutant_counts[0] += uncaught_counts[0]
                        if verbose:
                            logger.info(
                                magenta(
                                    f"Mutator {m.NAME} found {uncaught_counts[0]} uncaught revert mutants (out of {total_counts[0]} that compile)"
                                )
                            )
                    elif m.NAME == "CR":
                        total_mutant_counts[1] += total_counts[1]
                        uncaught_mutant_counts[1] += uncaught_counts[1]
                        if verbose:
                            logger.info(
                                magenta(
                                    f"Mutator {m.NAME} found {uncaught_counts[1]} uncaught comment mutants (out of {total_counts[1]} that compile)"
                                )
                            )
                    else:
                        total_mutant_counts[2] += total_counts[2]
                        uncaught_mutant_counts[2] += uncaught_counts[2]
                        if verbose:
                            logger.info(
                                magenta(
                                    f"Mutator {m.NAME} found {uncaught_counts[2]} uncaught tweak mutants (out of {total_counts[2]} that compile)"
                                )
                            )
                            logger.info(
                                magenta(
                                    f"Running total: found {uncaught_mutant_counts[2]} uncaught tweak mutants (out of {total_mutant_counts[2]} that compile)"
                                )
                            )

                    dont_mutate_lines = lines_list
                    if comprehensive_flag:
                        dont_mutate_lines = []

        except Exception as e:  # pylint: disable=broad-except
            logger.error(e)
            transfer_and_delete(files_dict)

        except KeyboardInterrupt:
            # transfer and delete the backup files if interrupted
            logger.error("\nExecution interrupted by user (Ctrl + C). Cleaning up...")
            transfer_and_delete(files_dict)

        # transfer and delete the backup files
        transfer_and_delete(files_dict)

        if target_contract == skip_flag:
            logger.debug(f"No target contracts found in {filename}, skipping")
            continue

        # log results for this file
        logger.info(blue(f"Done mutating {target_contract}."))
        if total_mutant_counts[0] > 0:
            logger.info(
                magenta(
                    f"Revert mutants: {uncaught_mutant_counts[0]} uncaught of {total_mutant_counts[0]} ({100 * uncaught_mutant_counts[0]/total_mutant_counts[0]}%)"
                )
            )
        else:
            logger.info(magenta("Zero Revert mutants analyzed"))

        if total_mutant_counts[1] > 0:
            logger.info(
                magenta(
                    f"Comment mutants: {uncaught_mutant_counts[1]} uncaught of {total_mutant_counts[1]} ({100 * uncaught_mutant_counts[1]/total_mutant_counts[1]}%)"
                )
            )
        else:
            logger.info(magenta("Zero Comment mutants analyzed"))

        if total_mutant_counts[2] > 0:
            logger.info(
                magenta(
                    f"Tweak mutants: {uncaught_mutant_counts[2]} uncaught of {total_mutant_counts[2]} ({100 * uncaught_mutant_counts[2]/total_mutant_counts[2]}%)\n"
                )
            )
        else:
            logger.info(magenta("Zero Tweak mutants analyzed\n"))

        # Reset mutant counts before moving on to the next file
        total_mutant_counts[0] = 0
        total_mutant_counts[1] = 0
        total_mutant_counts[2] = 0
        uncaught_mutant_counts[0] = 0
        uncaught_mutant_counts[1] = 0
        uncaught_mutant_counts[2] = 0

    # Print the total time elapsed in a human-readable time format
    elapsed_time = round(time.time() - start_time)
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        elapsed_string = f"{hours} {'hour' if hours == 1 else 'hours'}"
    elif minutes > 0:
        elapsed_string = f"{minutes} {'minute' if minutes == 1 else 'minutes'}"
    else:
        elapsed_string = f"{seconds} {'second' if seconds == 1 else 'seconds'}"

    logger.info(
        blue(f"Finished mutation testing assessment of '{args.codebase}' in {elapsed_string}\n")
    )


# endregion
