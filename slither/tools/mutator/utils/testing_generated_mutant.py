import logging
import sys
import subprocess
from pathlib import Path
from typing import Dict, Union
import crytic_compile
from slither.tools.mutator.utils.file_handling import create_mutant_file, reset_file
from slither.utils.colors import green, red, yellow

logger = logging.getLogger("Slither-Mutate")


def compile_generated_mutant(file_path: str, mappings: str) -> bool:
    """
    function to compile the generated mutant
    returns: status of compilation
    """
    try:
        crytic_compile.CryticCompile(file_path, solc_remaps=mappings)
        return True
    except:  # pylint: disable=bare-except
        return False


def run_test_cmd(
    cmd: str,
    timeout: Union[int, None] = None,
    target_file: Union[str, None] = None,
    verbose: bool = False,
) -> bool:
    """
    function to run codebase tests
    returns: boolean whether the tests passed or not
    """

    # add --fail-fast for foundry tests, to exit after first failure
    if "forge test" in cmd and "--fail-fast" not in cmd:
        cmd += " --fail-fast"
    # add --bail for hardhat and truffle tests, to exit after first failure
    elif "hardhat test" in cmd or "truffle test" in cmd and "--bail" not in cmd:
        cmd += " --bail"

    if timeout is None and "hardhat" not in cmd:  # hardhat doesn't support --force flag on tests
        # if no timeout, ensure all contracts are recompiled w/out using any cache
        cmd += " --force"

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,  # True: Raises a CalledProcessError if the return code is non-zero
        )

    except subprocess.TimeoutExpired:
        # Timeout, treat this as a test failure
        logger.info("Tests took too long, consider increasing the timeout")
        result = None  # or set result to a default value

    except KeyboardInterrupt:
        logger.info(yellow("Ctrl-C received"))
        if target_file is not None:
            logger.info("Restoring original files")
            reset_file(target_file)
        logger.info("Exiting")
        sys.exit(1)

    # if result is 0 then it is an uncaught mutant because tests didn't fail
    if result:
        code = result.returncode
        if code == 0:
            return True

    # If tests fail in verbose-mode, print both stdout and stderr for easier debugging
    if verbose:
        logger.info(yellow(result.stdout.decode("utf8")))
        logger.info(red(result.stderr.decode("utf8")))

    return False


# return 0 if uncaught, 1 if caught, and 2 if compilation fails
def test_patch(  # pylint: disable=too-many-arguments
    output_folder: Path,
    file: str,
    patch: Dict,
    command: str,
    generator_name: str,
    timeout: int,
    mappings: Union[str, None],
    verbose: bool,
) -> int:
    """
    function to verify whether each patch is caught by tests
    returns: 0 (uncaught), 1 (caught), or 2 (compilation failure)
    """
    with open(file, "r", encoding="utf8") as filepath:
        content = filepath.read()
    # Perform the replacement based on the index values
    replaced_content = content[: patch["start"]] + patch["new_string"] + content[patch["end"] :]
    # Write the modified content back to the file
    with open(file, "w", encoding="utf8") as filepath:
        filepath.write(replaced_content)

    if compile_generated_mutant(file, mappings):
        if run_test_cmd(command, timeout, file, False):

            create_mutant_file(output_folder, file, generator_name)
            logger.info(
                f"[{generator_name}] Line {patch['line_number']}: '{patch['old_string']}' ==> '{patch['new_string']}' --> UNCAUGHT"
            )
            reset_file(file)

            return 0  # uncaught
    else:
        if verbose:
            logger.info(
                yellow(
                    f"[{generator_name}] Line {patch['line_number']}: '{patch['old_string']}' ==> '{patch['new_string']}' --> COMPILATION FAILURE"
                )
            )

        reset_file(file)
        return 2  # compile failure

    if verbose:
        logger.info(
            green(
                f"[{generator_name}] Line {patch['line_number']}: '{patch['old_string']}' ==> '{patch['new_string']}' --> CAUGHT"
            )
        )

    reset_file(file)
    return 1  # caught
