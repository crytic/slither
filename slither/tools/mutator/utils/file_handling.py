import os
from typing import Dict, List
import logging

logger = logging.getLogger("Slither-Mutate")

duplicated_files = {}

def backup_source_file(source_code: Dict, output_folder: str) -> Dict:
    """
    function to backup the source file
    returns: dictionary of duplicated files
    """
    os.makedirs(output_folder, exist_ok=True)

    for file_path, content in source_code.items():
        directory, filename = os.path.split(file_path)
        new_filename = f"{output_folder}/backup_{filename}"
        new_file_path = os.path.join(directory, new_filename)

        with open(new_file_path, 'w', encoding="utf8") as new_file:
            new_file.write(content)
        duplicated_files[file_path] = new_file_path

    return duplicated_files

def transfer_and_delete(files_dict: Dict) -> None:
    """function to transfer the original content to the sol file after campaign"""
    try:
        files_dict_copy = files_dict.copy()
        for item, value in files_dict_copy.items():
            with open(value, 'r', encoding="utf8") as duplicated_file:
                content = duplicated_file.read()

            with open(item, 'w', encoding="utf8") as original_file:
                original_file.write(content)

            os.remove(value)

            # delete elements from the global dict
            del duplicated_files[item]

    except Exception as e: # pylint: disable=broad-except
        logger.error(f"Error transferring content: {e}")

def create_mutant_file(file: str, count: int, rule: str) -> None:
    """function to create new mutant file"""
    try:
        _, filename = os.path.split(file)
        # Read content from the duplicated file
        with open(file, 'r', encoding="utf8") as source_file:
            content = source_file.read()

        # Write content to the original file
        mutant_name = filename.split('.')[0]

        # create folder for each contract
        os.makedirs("mutation_campaign/" + mutant_name, exist_ok=True)
        with open("mutation_campaign/" + mutant_name + '/' + mutant_name + '_' + rule + '_' + str(count) + '.sol', 'w', encoding="utf8") as mutant_file:
            mutant_file.write(content)

        # reset the file
        with open(duplicated_files[file], 'r', encoding="utf8") as duplicated_file:
            duplicate_content = duplicated_file.read()

        with open(file, 'w', encoding="utf8") as source_file:
            source_file.write(duplicate_content)

    except Exception as e: # pylint: disable=broad-except
        logger.error(f"Error creating mutant: {e}")

def reset_file(file: str) -> None:
    """function to reset the file"""
    try:
        # directory, filename = os.path.split(file)
        # reset the file
        with open(duplicated_files[file], 'r', encoding="utf8") as duplicated_file:
            duplicate_content = duplicated_file.read()

        with open(file, 'w', encoding="utf8") as source_file:
            source_file.write(duplicate_content)

    except Exception as e: # pylint: disable=broad-except
        logger.error(f"Error resetting file: {e}")


def get_sol_file_list(codebase: str, ignore_paths: List[str] | None) -> List[str]:
    """
    function to get the contracts list
    returns: list of .sol files
    """
    sol_file_list = []
    if ignore_paths is None:
        ignore_paths = []
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
                _, dirname = os.path.split(filename)
                if dirname in ignore_paths:
                    continue
                for i in get_sol_file_list(filename, ignore_paths):
                    sol_file_list.append(i)

    return sol_file_list
