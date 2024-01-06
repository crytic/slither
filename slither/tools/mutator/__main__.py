import argparse
import inspect
import logging
import sys
from typing import Type, List, Any, Dict, Tuple
import os
import shutil

from crytic_compile import cryticparser

from slither import Slither
from slither.tools.mutator.mutators import all_mutators
from .mutators.abstract_mutator import AbstractMutator
from .utils.command_line import output_mutators
from .utils.file_handling import transfer_and_delete, backup_source_file, get_sol_file_list
from slither.utils.colors import yellow, magenta

logging.basicConfig()
logger = logging.getLogger("Slither-Mutate")
logger.setLevel(logging.INFO)

###################################################################################
###################################################################################
# region Cli Arguments
###################################################################################
###################################################################################

def parse_args() -> argparse.Namespace:
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

    # argument to add the test command
    parser.add_argument(
        "--test-cmd",
        help="Command line needed to run the tests for your project"
    )

    # argument to add the test directory - containing all the tests
    parser.add_argument(
        "--test-dir",
        help="Directory of tests"
    )

    # argument to ignore the interfaces, libraries
    parser.add_argument(
        "--ignore-dirs",
        help="Directories to ignore"
    )

    # to_do: add time out argument
    parser.add_argument(
        "--timeout",
        help="Set timeout for test command"
    )
    # Initiate all the crytic config cli options
    cryticparser.init(parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


def _get_mutators() -> List[Type[AbstractMutator]]:
    detectors_ = [getattr(all_mutators, name) for name in dir(all_mutators)]
    detectors = [c for c in detectors_ if inspect.isclass(c) and issubclass(c, AbstractMutator)]
    return detectors


class ListMutators(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self, parser: Any, *args: Any, **kwargs: Any
    ) -> None:  # pylint: disable=signature-differs
        checks = _get_mutators()
        output_mutators(checks)
        parser.exit()


# endregion
###################################################################################
###################################################################################
# region Main
###################################################################################
###################################################################################

def main() -> None:
    args = parse_args()
    # print(os.path.isdir(args.codebase)) # provided file/folder

    # arguments
    test_command: str = args.test_cmd
    test_directory: str = args.test_dir
    paths_to_ignore: str | None = args.ignore_dirs
    timeout: int = args.timeout
    
    print(magenta(f"Starting Mutation Campaign in '{args.codebase} \n"))

    if paths_to_ignore:
        paths_to_ignore_list = paths_to_ignore.strip('][').split(',')
        print(magenta(f"Ignored paths - {', '.join(paths_to_ignore_list)} \n"))
    else:
        paths_to_ignore_list = []

    # get all the contracts as a list from given codebase 
    sol_file_list: List[str] = get_sol_file_list(args.codebase, paths_to_ignore_list)

    # folder where backup files and valid mutants created
    output_folder = os.getcwd() + "/mutation_campaign"
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)

    for filename in sol_file_list:
        contract_name = os.path.split(filename)[1].split('.sol')[0]
        # slither object
        sl = Slither(filename, **vars(args))

        # create a backup files 
        files_dict = backup_source_file(sl.source_code, output_folder)

        # total count of mutants
        total_count = 0

        # count of valid mutants
        v_count = 0

        # mutation
        try:
            for compilation_unit_of_main_file in sl.compilation_units:
            # compilation_unit_of_main_file = sl.compilation_units[-1]
                # for i in compilation_unit_of_main_file.contracts:
                #     print(i.name)
                for M in _get_mutators():
                    m = M(compilation_unit_of_main_file)
                    count_valid, count_invalid = m.mutate(test_command, test_directory, contract_name)
                    v_count += count_valid
                    total_count += count_valid + count_invalid
        except Exception as e:
            logger.error(e)

        except KeyboardInterrupt:
            # transfer and delete the backup files if interrupted
            logger.error("\nExecution interrupted by user (Ctrl + C). Cleaning up...")
            transfer_and_delete(files_dict)
        
        # transfer and delete the backup files
        transfer_and_delete(files_dict)
    
        # output
        print(yellow(f"Done mutating, '{filename}'. Valid mutant count: '{v_count}' and Total mutant count '{total_count}'.\n"))

    print(magenta(f"Finished Mutation Campaign in '{args.codebase}' \n"))
# endregion
 