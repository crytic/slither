import os
import difflib
from collections import defaultdict

from slither.core.compilation_unit import SlitherCompilationUnit


def create_patch(
    result: dict,
    file: str,
    start: int,
    end: int,
    old_str: str | bytes,
    new_str: str | bytes,
) -> None:
    if isinstance(old_str, bytes):
        old_str = old_str.decode("utf8")
    if isinstance(new_str, bytes):
        new_str = new_str.decode("utf8")
    p = {"start": start, "end": end, "old_string": old_str, "new_string": new_str}
    if "patches" not in result:
        result["patches"] = defaultdict(list)
    if p not in result["patches"][file]:
        result["patches"][file].append(p)


def apply_patch(original_txt: bytes, patch: dict, offset: int) -> tuple[bytes, int]:
    patched_txt = original_txt[: int(patch["start"] + offset)]
    patched_txt += patch["new_string"].encode("utf8")
    patched_txt += original_txt[int(patch["end"] + offset) :]

    # Keep the diff of text added or sub, in case of multiple patches
    # Note: must use byte length since patch offsets are byte offsets from solc
    patch_length_diff = len(patch["new_string"].encode("utf8")) - (patch["end"] - patch["start"])
    return patched_txt, patch_length_diff + offset


def create_diff(
    compilation_unit: SlitherCompilationUnit, original_txt: bytes, patched_txt: bytes, filename: str
) -> str:
    if compilation_unit.crytic_compile:
        relative_path = compilation_unit.crytic_compile.filename_lookup(filename).relative
        relative_path = os.path.join(".", relative_path)
    else:
        relative_path = filename
    diff = difflib.unified_diff(
        original_txt.decode("utf8").splitlines(False),
        patched_txt.decode("utf8").splitlines(False),
        fromfile=relative_path,
        tofile=relative_path,
        lineterm="",
    )

    return "\n".join(list(diff)) + "\n"
