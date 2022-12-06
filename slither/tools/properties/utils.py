import logging
from pathlib import Path

from slither.utils.colors import green, yellow

logger = logging.getLogger("Slither")


def write_file(
    output_dir: Path,
    filename: str,
    content: str,
    allow_overwrite: bool = True,
    discard_if_exist: bool = False,
) -> None:
    """
    Write the content into output_dir/filename
    :param output_dir:
    :param filename:
    :param content:
    :param allow_overwrite: If true, allows to overwrite existing file (default: true). Emit warning if overwrites
    :param discard_if_exist: If true, it will not emit warning or overwrite the file if it exists, (default: False)
    :return:
    """
    file_to_write = Path(output_dir, filename)
    if file_to_write.exists():
        if discard_if_exist:
            return
        if not allow_overwrite:
            logger.info(yellow(f"{file_to_write} already exist and will not be overwritten"))
            return
        logger.info(yellow(f"Overwrite {file_to_write}"))
    else:
        logger.info(green(f"Write {file_to_write}"))
    with open(file_to_write, "w", encoding="utf8") as f:
        f.write(content)
