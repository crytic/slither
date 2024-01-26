from typing import Dict, Union
from collections import defaultdict


# pylint: disable=too-many-arguments
def create_patch_with_line(
    result: Dict,
    file: str,
    start: int,
    end: int,
    old_str: Union[str, bytes],
    new_str: Union[str, bytes],
    line_no: int,
) -> None:
    if isinstance(old_str, bytes):
        old_str = old_str.decode("utf8")
    if isinstance(new_str, bytes):
        new_str = new_str.decode("utf8")
    p = {
        "start": start,
        "end": end,
        "old_string": old_str,
        "new_string": new_str,
        "line_number": line_no,
    }
    if "patches" not in result:
        result["patches"] = defaultdict(list)
    if p not in result["patches"][file]:
        result["patches"][file].append(p)
