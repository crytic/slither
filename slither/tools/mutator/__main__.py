import argparse
import inspect
import logging
import sys
import os
import shutil
from typing import Type, List, Any, Optional
from crytic_compile import cryticparser
from slither import Slither
from slither.tools.mutator.mutators import all_mutators
from slither.utils.colors import yellow, magenta
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
        "--verbose",
        help="output all mutants generated",
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
        "--quick",
        help="to stop full mutation if revert mutator passes",
        action="store_true",
        default=False,
    )

    # Initiate all the crytic config cli options
    cryticparser.init(parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


def _get_mutators(mutators_list: List[str] | None) -> List[Type[AbstractMutator]]:
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


def main() -> (None):  # pylint: disable=too-many-statements,too-many-branches,too-many-locals
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
    contract_names: Optional[List[str]] = args.contract_names
    quick_flag: Optional[bool] = args.quick

    logger.info(magenta(f"Starting Mutation Campaign in '{args.codebase} \n"))

    if paths_to_ignore:
        paths_to_ignore_list = paths_to_ignore.strip("][").split(",")
        logger.info(magenta(f"Ignored paths - {', '.join(paths_to_ignore_list)} \n"))
    else:
        paths_to_ignore_list = []

    # get all the contracts as a list from given codebase
    sol_file_list: List[str] = get_sol_file_list(args.codebase, paths_to_ignore_list)

    # folder where backup files and valid mutants created
    if output_dir is None:
        output_dir = "/mutation_campaign"
    output_folder = os.getcwd() + output_dir
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)

    # set default timeout
    if timeout is None:
        timeout = 30

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

    for filename in sol_file_list:  # pylint: disable=too-many-nested-blocks
        contract_name = os.path.split(filename)[1].split(".sol")[0]
        # slither object
        sl = Slither(filename, **vars(args))
        # create a backup files
        files_dict = backup_source_file(sl.source_code, output_folder)
        # total revert/comment/tweak mutants that were generated and compiled
        total_mutant_counts = [0, 0, 0]
        # total valid revert/comment/tweak mutants
        valid_mutant_counts = [0, 0, 0]
        # lines those need not be mutated (taken from RR and CR)
        dont_mutate_lines = []

        # mutation
        contract_instance = ''
        try:
            for compilation_unit_of_main_file in sl.compilation_units:
                for contract in compilation_unit_of_main_file.contracts:
                    if contract_names is not None and contract.name in contract_names:
                        contract_instance = contract
                    elif contract_names is not None and contract.name not in contract_names:
                        contract_instance = "SLITHER_SKIP_MUTATIONS"
                    elif str(contract.name).lower() == contract_name.lower():
                        contract_instance = contract

                if contract_instance == '':
                    logger.info(f"Cannot find contracts in file {filename}, try specifying them with --contract-names")
                    continue

                if contract_instance == 'SLITHER_SKIP_MUTATIONS':
                    logger.debug(f"Skipping mutations in {filename}")
                    continue

                logger.info(yellow(f"Mutating contract {contract_instance}"))
                for M in mutators_list:
                    m = M(
                        compilation_unit_of_main_file,
                        int(timeout),
                        test_command,
                        test_directory,
                        contract_instance,
                        solc_remappings,
                        verbose,
                        output_folder,
                        dont_mutate_lines,
                    )
                    (total_counts, valid_counts, lines_list) = m.mutate()
                    total_mutant_counts[0] += total_counts[0]
                    total_mutant_counts[1] += total_counts[1]
                    total_mutant_counts[2] += total_counts[2]
                    valid_mutant_counts[0] += valid_counts[0]
                    valid_mutant_counts[1] += valid_counts[1]
                    valid_mutant_counts[2] += valid_counts[2]
                    dont_mutate_lines = lines_list
                    if not quick_flag:
                        dont_mutate_lines = []
        except Exception as e:  # pylint: disable=broad-except
            logger.error(e)

        except KeyboardInterrupt:
            # transfer and delete the backup files if interrupted
            logger.error("\nExecution interrupted by user (Ctrl + C). Cleaning up...")
            transfer_and_delete(files_dict)

        if not contract_instance == 'SLITHER_SKIP_MUTATIONS':
            # transfer and delete the backup files
            transfer_and_delete(files_dict)
            # output
            print(yellow(f"Done mutating {filename}."))
            if total_mutant_counts[0] > 0:
                print(yellow(f"Revert mutants: {valid_mutant_counts[0]} valid of {total_mutant_counts[0]} ({100 * valid_mutant_counts[0]/total_mutant_counts[0]}%)"))
            else:
                print(yellow("Zero Revert mutants analyzed"))

            if total_mutant_counts[1] > 0:
                print(yellow(f"Comment mutants: {valid_mutant_counts[1]} valid of {total_mutant_counts[1]} ({100 * valid_mutant_counts[1]/total_mutant_counts[1]}%)"))
            else:
                print(yellow("Zero Comment mutants analyzed"))

            if total_mutant_counts[2] > 0:
                print(yellow(f"Tweak mutants: {valid_mutant_counts[2]} valid of {total_mutant_counts[2]} ({100 * valid_mutant_counts[2]/total_mutant_counts[2]}%)"))
            else:
                print(yellow("Zero Tweak mutants analyzed"))

# endregion
