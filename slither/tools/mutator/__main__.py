import argparse
import inspect
import logging
import sys
import os
import shutil
from typing import Type, List, Any
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

    # time out argument
    parser.add_argument(
        "--timeout",
        help="Set timeout for test command (by default 30 seconds)"
    )

    # output directory argument
    parser.add_argument(
        "--output-dir",
        help="Output Directory (by default 'mutation_campaign')"
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
    if not mutators_list is None:
        detectors = [c for c in detectors_ if inspect.isclass(c) and issubclass(c, AbstractMutator) and str(c.NAME) in mutators_list ]
    else:
        detectors = [c for c in detectors_ if inspect.isclass(c) and issubclass(c, AbstractMutator) ]
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

    # arguments
    test_command: str = args.test_cmd
    test_directory: str = args.test_dir
    paths_to_ignore: str | None = args.ignore_dirs
    output_dir: str | None = args.output_dir
    timeout: int | None = args.timeout
    solc_remappings: str | None = args.solc_remaps
    verbose: bool = args.verbose
    mutators_to_run: List[str] | None = args.mutators_to_run 
    contract_names: List[str] | None = args.contract_names
    quick_flag: bool = args.quick
    
    print(magenta(f"Starting Mutation Campaign in '{args.codebase} \n"))

    if paths_to_ignore:
        paths_to_ignore_list = paths_to_ignore.strip('][').split(',')
        print(magenta(f"Ignored paths - {', '.join(paths_to_ignore_list)} \n"))
    else:
        paths_to_ignore_list = []

    # get all the contracts as a list from given codebase 
    sol_file_list: List[str] = get_sol_file_list(args.codebase, paths_to_ignore_list)

    # folder where backup files and valid mutants created
    if output_dir == None:
        output_dir = "/mutation_campaign"
    output_folder = os.getcwd() + output_dir
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)

    # set default timeout
    if timeout == None:
        timeout = 30

    # setting RR mutator as first mutator
    mutators_list = _get_mutators(mutators_to_run)
    for M in mutators_list:
        if M.NAME == "RR":
            mutators_list.remove(M)
            mutators_list.insert(0, M)

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
                contract_instance = ''
                for contract in compilation_unit_of_main_file.contracts:
                    if contract_names != None and contract.name in contract_names:
                        contract_instance = contract
                    elif str(contract.name).lower() == contract_name.lower():
                        contract_instance = contract
                if contract_instance == '':
                    logger.error("Can't find the contract")
                else:
                    for M in mutators_list:
                        m = M(compilation_unit_of_main_file, int(timeout), test_command, test_directory, contract_instance, solc_remappings, verbose, output_folder)
                        count_valid, count_invalid = m.mutate()
                        v_count += count_valid
                        total_count += count_valid + count_invalid
                        if quick_flag:
                            if str(m.NAME) == 'RR' and v_count > 0:
                                break
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
 