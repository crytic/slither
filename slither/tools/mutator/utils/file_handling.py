import os
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger("Slither-Mutate")

# function to backup the source file 
def backup_source_file(source_code: Dict, output_folder: str) -> Dict:
    duplicated_files = {}
    os.makedirs(output_folder, exist_ok=True)
    
    for file_path, content in source_code.items():
        directory, filename = os.path.split(file_path)
        new_filename = f"{output_folder}/backup_{filename}"
        new_file_path = os.path.join(directory, new_filename)

        with open(new_file_path, 'w') as new_file:
            new_file.write(content)
        duplicated_files[file_path] = new_file_path

    return duplicated_files

# function to transfer the original content to the sol file after campaign
def transfer_and_delete(files_dict: Dict) -> None:
    try:
        for item, value in files_dict.items(): 
            with open(value, 'r') as duplicated_file:
                content = duplicated_file.read()

            with open(item, 'w') as original_file:
                original_file.write(content)

            os.remove(value)
    except Exception as e:
        logger.error(f"Error transferring content: {e}")

#function to create new mutant file
def create_mutant_file(file: str, count: int, rule: str) -> None:
    try:
        directory, filename = os.path.split(file)
        # Read content from the duplicated file
        with open(file, 'r') as source_file:
            content = source_file.read()

        # Write content to the original file
        mutant_name = filename.split('.')[0]
        with open("mutation_campaign/" + mutant_name + '_' + rule + '_' + str(count) + '.sol', 'w') as mutant_file:
            mutant_file.write(content)

    except Exception as e:
        logger.error(f"Error creating mutant: {e}")

# function to get the contracts list
def get_sol_file_list(codebase: str, ignore_paths: List[str]) -> List[str]:
    sol_file_list = []

    # if input is contract file
    if os.path.isfile(codebase):
        return [codebase]
    
    # if input is folder
    elif os.path.isdir(codebase):
        directory = os.path.abspath(codebase)
        for file in os.listdir(directory):
            filename = os.path.join(directory, file)
            if os.path.isfile(filename):
                sol_file_list.append(filename)
            elif os.path.isdir(filename):
                directory_name, dirname = os.path.split(filename)
                if dirname in ignore_paths:
                    continue 
                for i in get_sol_file_list(filename, ignore_paths):
                    sol_file_list.append(i)

    return sol_file_list 
# to_do: create a function to delete the commands from the sol file
# def remove_comments(self) -> None: