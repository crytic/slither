import subprocess
import os
import logging
import time
import signal
from typing import Dict
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


def run_test_cmd(cmd: str, test_dir: str, timeout: int) -> bool:
    """
    function to run codebase tests
    returns: boolean whether the tests passed or not
    """
    # future purpose
    _ = test_dir
    # add --fail-fast for foundry tests, to exit after first failure
    if "forge test" in cmd and "--fail-fast" not in cmd:
        cmd += " --fail-fast"
    # add --bail for hardhat and truffle tests, to exit after first failure
    elif "hardhat test" in cmd or "truffle test" in cmd and "--bail" not in cmd:
        cmd += " --bail"

    start = time.time()

    # starting new process
    with subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as P:
        try:
            # checking whether the process is completed or not within 30 seconds(default)
            while P.poll() is None and (time.time() - start) < timeout:
                time.sleep(0.05)
        finally:
            if P.poll() is None:
                logger.error("HAD TO TERMINATE ANALYSIS (TIMEOUT OR EXCEPTION)")
                # sends a SIGTERM signal to process group - bascially killing the process
                os.killpg(os.getpgid(P.pid), signal.SIGTERM)
                # Avoid any weird race conditions from grabbing the return code
                time.sleep(0.05)
            # indicates whether the command executed sucessfully or not
            r = P.returncode

    # if r is 0 then it is valid mutant because tests didn't fail
    return r == 0


def test_patch(  # pylint: disable=too-many-arguments
    file: str,
    patch: Dict,
    command: str,
    index: int,
    generator_name: str,
    timeout: int,
    mappings: str | None,
    verbose: bool,
) -> bool:
    """
    function to verify the validity of each patch
    returns: valid or invalid patch
    """
    with open(file, "r", encoding="utf-8") as filepath:
        content = filepath.read()
    # Perform the replacement based on the index values
    replaced_content = content[: patch["start"]] + patch["new_string"] + content[patch["end"] :]
    # Write the modified content back to the file
    with open(file, "w", encoding="utf-8") as filepath:
        filepath.write(replaced_content)
    if compile_generated_mutant(file, mappings):
        if run_test_cmd(command, file, timeout):
            create_mutant_file(file, index, generator_name)
            logger.info(
                red(
                    f"[{generator_name}] Line {patch['line_number']}: '{patch['old_string']}' ==> '{patch['new_string']}' --> VALID"
                )
            )
            reset_file(file)
            return 0 # valid
    else:
        if verbose:
            logger.info(
                yellow(
                    f"[{generator_name}] Line {patch['line_number']}: '{patch['old_string']}' ==> '{patch['new_string']}' --> COMPILATION FAILURE"
                )
            )
        reset_file(file)
        return 2 # compile failure

    if verbose:
        logger.info(
            green(
                f"[{generator_name}] Line {patch['line_number']}: '{patch['old_string']}' ==> '{patch['new_string']}' --> INVALID"
            )
        )
    reset_file(file)
    return 1 # invalid
