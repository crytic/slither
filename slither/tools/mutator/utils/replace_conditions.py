import logging

logger = logging.getLogger("Slither-Mutate")

# function to replace the string
def replace_string_in_source_file(file_path: str, old_string: str, new_string: str) -> None:
    try:
        # Read the content of the Solidity file
        with open(file_path, 'r') as file:
            content = file.read()

        # Perform the string replacement
        modified_content = content.replace(old_string, new_string)

        # Write the modified content back to the file
        with open(file_path, 'w') as file:
            file.write(modified_content)

        logger.info(f"String '{old_string}' replaced with '{new_string}' in '{file_path}'.")
    except Exception as e:
        logger.error(f"Error replacing string: {e}")

# function to replace the string in a specific line 
def replace_string_in_source_file_specific_line(file_path: str, old_string: str, new_string: str, line_number : int) -> None:
    try:
        # Read the content of the Solidity file
        with open(file_path, 'r') as file:
            lines = file.readlines()

        if 1 <= line_number <= len(lines):
            # Replace the old string with the new string on the specified line
            lines[line_number - 1] = lines[line_number - 1].replace(old_string, new_string)

            # Write the modified content back to the file
            with open(file_path, 'w') as file:
                file.writelines(lines)

            logger.info(f"String '{old_string}' replaced with '{new_string}' in '{file_path}'.' at '{line_number}")
        else:
            logger.error(f'Error: Line number {line_number} is out of range')

    except Exception as e:
        logger.erro(f'Error: {e}')