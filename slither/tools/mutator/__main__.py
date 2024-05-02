import inspect
import logging
import os
import shutil
import time
from pathlib import Path
import typer
from typing import Type, List, Optional, Annotated, Union

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
from slither.__main__ import app
from slither.utils.command_line import (
    target_type,
    SlitherState,
    SlitherApp,
    GroupWithCrytic,
    CommaSeparatedValueParser,
)

mutate_cmd: SlitherApp = SlitherApp()
app.add_typer(mutate_cmd, name="mutate")

logging.basicConfig()
logger = logging.getLogger("Slither-Mutate")
logger.setLevel(logging.INFO)


###################################################################################
###################################################################################
# region Cli Arguments
###################################################################################
###################################################################################


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


def list_mutator_action(ctx: typer.Context, value: bool) -> None:
    """List mutators."""
    if not value or ctx.resilient_parsing:
        return

    checks = _get_mutators(None)
    output_mutators(checks)
    raise typer.Exit()


# endregion
###################################################################################
###################################################################################
# region Main
###################################################################################
###################################################################################


@mutate_cmd.callback(cls=GroupWithCrytic)
def main(
    ctx: typer.Context,
    codebase: Annotated[Path, typer.Argument(help="Codebase directory.")],
    test_command: Annotated[
        str, typer.Option("--test-cmd", help="Command to run the tests for your project.")
    ],
    test_directory: Annotated[
        Optional[str], typer.Option("--test-dir", help="Tests directory.")
    ] = None,
    output_dir: Annotated[
        Optional[Path], typer.Option("--output-dir", help="Output directory.")
    ] = Path("mutation_campaign"),
    paths_to_ignore: Annotated[
        Optional[str], typer.Option("--ignore-dirs", help="Directories to ignore.")
    ] = None,
    timeout: Annotated[int, typer.Option("--timeout", help="Test timeout.")] = 30,
    list_mutators: Annotated[
        bool,
        typer.Option(
            "--list-mutators", is_eager=True, help="List mutators.", callback=list_mutator_action
        ),
    ] = False,
    mutators_to_run: Annotated[
        Optional[str], typer.Option(help="Mutant generators to run.")
    ] = None,
    verbose_count: Annotated[int, typer.Option("--verbose", "-v", count=True, max=2)] = 0,
    contract_names: Annotated[
        List[str],
        typer.Option(
            help="List of contract names you want to mutate", click_type=CommaSeparatedValueParser()
        ),
    ] = None,
    comprehensive_flag: Annotated[
        bool, typer.Option(help="Continue testing minor mutations if severe mutants are uncaught.")
    ] = False,
) -> None:  # pylint: disable=too-many-statements,too-many-branches,too-many-locals
    """Experimental smart contract mutator. Based on https://arxiv.org/abs/2006.11597."""

    # arguments
    # test_command: str = args.test_cmd
    state = ctx.ensure_object(SlitherState)
    solc_remappings: Optional[str] = state.get("solc_remaps")

    verbose = False
    very_verbose = False
    if verbose_count >= 1:
        verbose = True
    if verbose_count >= 2:
        very_verbose = True

    logger.info(blue(f"Starting mutation campaign in {codebase}"))

    if paths_to_ignore:
        paths_to_ignore_list = paths_to_ignore.strip("][").split(",")
        logger.info(blue(f"Ignored paths - {', '.join(paths_to_ignore_list)}"))
    else:
        paths_to_ignore_list = []

    # get all the contracts as a list from given codebase
    sol_file_list: List[str] = get_sol_file_list(codebase, paths_to_ignore_list)

    # folder where backup files and uncaught mutants are saved
    output_folder = output_dir.resolve()
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
        sl = Slither(filename, **state)
        # create a backup files
        files_dict = backup_source_file(sl.source_code, output_folder)
        # total revert/comment/tweak mutants that were generated and compiled
        total_mutant_counts = [0, 0, 0]
        # total uncaught revert/comment/tweak mutants
        uncaught_mutant_counts = [0, 0, 0]
        # lines those need not be mutated (taken from RR and CR)
        dont_mutate_lines = []

        # mutation
        target_contract = "SLITHER_SKIP_MUTATIONS" if contract_names else ""
        try:
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

                if target_contract == "SLITHER_SKIP_MUTATIONS":
                    logger.debug(f"Skipping mutations in {filename}")
                    continue

                # TODO: find a more specific way to omit interfaces
                # Ideally, we wouldn't depend on naming conventions
                if target_contract.name.startswith("I"):
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
                        very_verbose,
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

        # log results for this file
        logger.info(blue(f"Done mutating {target_contract}."))
        if total_mutant_counts[0] > 0:
            logger.info(
                magenta(
                    f"Revert mutants: {uncaught_mutant_counts[0]} uncaught of {total_mutant_counts[0]} ({100 * uncaught_mutant_counts[0] / total_mutant_counts[0]}%)"
                )
            )
        else:
            logger.info(magenta("Zero Revert mutants analyzed"))

        if total_mutant_counts[1] > 0:
            logger.info(
                magenta(
                    f"Comment mutants: {uncaught_mutant_counts[1]} uncaught of {total_mutant_counts[1]} ({100 * uncaught_mutant_counts[1] / total_mutant_counts[1]}%)"
                )
            )
        else:
            logger.info(magenta("Zero Comment mutants analyzed"))

        if total_mutant_counts[2] > 0:
            logger.info(
                magenta(
                    f"Tweak mutants: {uncaught_mutant_counts[2]} uncaught of {total_mutant_counts[2]} ({100 * uncaught_mutant_counts[2] / total_mutant_counts[2]}%)\n"
                )
            )
        else:
            logger.info(magenta("Zero Tweak mutants analyzed\n"))

        # Reset mutant counts before moving on to the next file
        if very_verbose:
            logger.info(blue("Reseting mutant counts to zero"))
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

    logger.info(blue(f"Finished mutation testing assessment of '{codebase}' in {elapsed_string}\n"))


# endregion
