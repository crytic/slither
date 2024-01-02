import crytic_compile
import subprocess
import os
import logging

logger = logging.getLogger("Slither-Mutate")

# function to compile the generated mutant
def compile_generated_mutant(file_path: str) -> bool:
    try:
        crytic_compile.CryticCompile(file_path)
        return True
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error Crytic Compile", e)

# function to run the tests
def run_test_suite(cmd: str, dir: str) -> bool:
    try:
        # Change to the foundry folder
        # os.chdir(dir)

        result = subprocess.run(cmd.split(' '), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not result.stderr:
            return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing 'forge test': {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False