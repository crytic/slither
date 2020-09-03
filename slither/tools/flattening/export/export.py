import json
import logging

# https://docs.python.org/3/library/zipfile.html#zipfile-objects
import zipfile
from collections import namedtuple
from typing import List

ZIP_TYPES_ACCEPTED = {
    "lzma": zipfile.ZIP_LZMA,
    "stored": zipfile.ZIP_STORED,
    "deflated": zipfile.ZIP_DEFLATED,
    "bzip2": zipfile.ZIP_BZIP2,
}

Export = namedtuple("Export", ["filename", "content"])

logger = logging.getLogger("Slither")


def save_to_zip(files: List[Export], zip_filename: str, zip_type: str = "lzma"):
    """
    Save projects to a zip
    """
    logger.info(f"Export {zip_filename}")
    with zipfile.ZipFile(
        zip_filename,
        "w",
        compression=ZIP_TYPES_ACCEPTED.get(zip_type, zipfile.ZIP_LZMA),
    ) as file_desc:
        for f in files:
            file_desc.writestr(str(f.filename), f.content)


def save_to_disk(files: List[Export]):
    """
    Save projects to a zip
    """
    for file in files:
        with open(file.filename, "w") as f:
            logger.info(f"Export {file.filename}")
            f.write(file.content)


def export_as_json(files: List[Export], filename: str):
    """
    Save projects to a zip
    """

    files_as_dict = {str(f.filename): f.content for f in files}

    if filename == "-":
        print(json.dumps(files_as_dict))
    else:
        logger.info(f"Export {filename}")
        with open(filename, "w") as f:
            json.dump(files_as_dict, f)
