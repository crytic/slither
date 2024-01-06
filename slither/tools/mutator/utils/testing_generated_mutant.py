import crytic_compile
import subprocess
import os
import logging
import time
import signal
from typing import List, Dict
from slither.tools.mutator.utils.file_handling import create_mutant_file, reset_file
from slither.utils.colors import green, red
logger = logging.getLogger("Slither-Mutate")
timeout = 30 # we can get it as parameter

# function to compile the generated mutant
def compile_generated_mutant(file_path: str) -> bool:
    try:
        crytic_compile.CryticCompile(file_path)
        return True
    except Exception as e:  # pylint: disable=broad-except
        print(True)
        # logger.error("Error Crytic Compile")
        return False

# function to run the tests
def run_test_suite(cmd: str, dir: str) -> bool:
    try:
        # Change to the foundry folder
        # os.chdir(dir)

        result = subprocess.run(cmd.split(' '), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # result = subprocess.run(cmd.split(' '), check=True)
        if not result.stderr:
            return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing '{cmd}': {e}")
        
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False
    
def run_test_cmd(cmd: str, dir: str) -> bool:
    start = time.time()

    # starting new process
    P = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)

    try:
        # checking whether the process is completed or not for 30 seconds
        while P.poll() is None and (time.time() - start) < timeout:
            time.sleep(0.05)
    finally:
        if P.poll() is None:
            print()
            print("HAD TO TERMINATE ANALYSIS (TIMEOUT OR EXCEPTION)")
            # sends a SIGTERM signal to process group - bascially killing the process
            os.killpg(os.getpgid(P.pid), signal.SIGTERM) 
            # Avoid any weird race conditions from grabbing the return code
            time.sleep(0.05)
        # indicates whether the command executed sucessfully or not
        r = P.returncode

    # if r is 0 then it is valid mutant because tests didn't fail
    return True if r == 0 else False

def test_patch(file: str, patch: Dict, command: str, index: int, generator_name: str) -> bool:
    with open(file, 'r') as filepath:
        content = filepath.read()
    # Perform the replacement based on the index values
    replaced_content = content[:patch['start']] + patch['new_string'] + content[patch['end']:]
    
    # Write the modified content back to the file
    with open(file, 'w') as filepath:
        filepath.write(replaced_content)
    if(compile_generated_mutant(file)):
        if(run_test_cmd(command, file)):
            create_mutant_file(file, index, generator_name)
            logger.info(green(f"String '{patch['old_string']}' replaced with '{patch['new_string']}' at line no. '{patch['line_number']}' in '{file}' ---> VALID\n"))
            return True
        
    reset_file(file)
    logger.info(red(f"String '{patch['old_string']}' replaced with '{patch['new_string']}' at line no. '{patch['line_number']}' in '{file}' ---> INVALID\n"))
    return False  