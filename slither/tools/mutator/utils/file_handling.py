import traceback
import logging
from pathlib import Path
import hashlib

logger = logging.getLogger("Slither-Mutate")

HashedPath = str
backuped_files: dict[str, HashedPath] = {}


def backup_source_file(source_code: dict, output_folder: Path) -> dict[str, HashedPath]:
    """
    function to backup the source file
    returns: dictionary of duplicated files
    """
    output_folder.mkdir(exist_ok=True, parents=True)
    for file_path, content in source_code.items():
        path_hash = hashlib.md5(bytes(file_path, "utf8")).hexdigest()
        (output_folder / path_hash).write_text(content, encoding="utf8")

        backuped_files[file_path] = (output_folder / path_hash).as_posix()

    return backuped_files


def transfer_and_delete(files_dict: dict[str, HashedPath]) -> None:
    """function to transfer the original content to the sol file after campaign"""
    try:
        files_dict_copy = files_dict.copy()
        for original_path, hashed_path in files_dict_copy.items():
            with open(hashed_path, encoding="utf8") as duplicated_file:
                content = duplicated_file.read()

            with open(original_path, "w", encoding="utf8") as original_file:
                original_file.write(content)

            Path(hashed_path).unlink()

            # delete elements from the global dict
            del backuped_files[original_path]

    except FileNotFoundError as e:
        logger.error("Error transferring content: %s", e)


global_counter = {}


def create_mutant_file(output_folder: Path, file: str, rule: str) -> None:
    """function to create new mutant file"""
    try:
        if rule not in global_counter:
            global_counter[rule] = 0

        file_path = Path(file)
        # Read content from the duplicated file
        content = file_path.read_text(encoding="utf8")

        # Write content to the original file
        mutant_name = file_path.stem
        # create folder for each contract
        mutation_dir = output_folder / mutant_name
        mutation_dir.mkdir(parents=True, exist_ok=True)

        mutation_filename = f"{mutant_name}_{rule}_{global_counter[rule]}.sol"
        with (mutation_dir / mutation_filename).open("w", encoding="utf8") as mutant_file:
            mutant_file.write(content)
        global_counter[rule] += 1

        # reset the file
        duplicate_content = Path(backuped_files[file]).read_text("utf8")

        with open(file, "w", encoding="utf8") as source_file:
            source_file.write(duplicate_content)

    except Exception as e:
        logger.error(f"Error creating mutant: {e}")
        traceback_str = traceback.format_exc()
        logger.error(traceback_str)  # Log the stack trace


def reset_file(file: str) -> None:
    """function to reset the file"""
    try:
        # reset the file
        with open(backuped_files[file], encoding="utf8") as duplicated_file:
            duplicate_content = duplicated_file.read()

        with open(file, "w", encoding="utf8") as source_file:
            source_file.write(duplicate_content)

    except Exception as e:
        logger.error("Error resetting file: %s", e)


def get_sol_file_list(codebase: Path, ignore_paths: list[str] | None) -> list[str]:
    """
    function to get the contracts list
    returns: list of .sol files
    """
    sol_file_list = []
    if ignore_paths is None:
        ignore_paths = []

    # if input is contract file
    if codebase.is_file():
        return [codebase.as_posix()]

    # if input is folder
    if codebase.is_dir():
        for file_name in codebase.rglob("*.sol"):
            if file_name.is_file() and not any(part in ignore_paths for part in file_name.parts):
                sol_file_list.append(file_name.as_posix())

    return sol_file_list
