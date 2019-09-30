import os
import difflib
from collections import defaultdict

def create_patch(result, file, start, end, old_str, new_str):
    if isinstance(old_str, bytes):
        old_str = old_str.decode('utf8')
    if isinstance(new_str, bytes):
        new_str = new_str.decode('utf8')
    p = {"start": start,
         "end": end,
         "old_string": old_str,
         "new_string": new_str
    }
    if 'patches' not in result:
        result['patches'] = defaultdict(list)
    if p not in result['patches'][file]:
        result['patches'][file].append(p)


def apply_patch(original_txt, patch, offset):
    patched_txt = original_txt[:int(patch['start'] + offset)]
    patched_txt += patch['new_string'].encode('utf8')
    patched_txt += original_txt[int(patch['end'] + offset):]

    # Keep the diff of text added or sub, in case of multiple patches
    patch_length_diff = len(patch['new_string']) - (patch['end'] - patch['start'])
    return patched_txt, patch_length_diff + offset


def create_diff(slither, original_txt, patched_txt, filename):
    if slither.crytic_compile:
        relative_path = slither.crytic_compile.filename_lookup(filename).relative
        relative_path = os.path.join('.', relative_path)
    else:
        relative_path = filename
    diff = difflib.unified_diff(original_txt.decode('utf8').splitlines(False),
                                patched_txt.decode('utf8').splitlines(False),
                                fromfile=relative_path,
                                tofile=relative_path,
                                lineterm='')

    return '\n'.join(list(diff)) + '\n'
