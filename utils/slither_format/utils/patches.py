import difflib
from collections import defaultdict

def create_patch(result, file, start, end, old_str, new_str):
    p = {"start": start,
         "end": end,
         "old_string": old_str,
         "new_string": new_str
    }
    if 'patches' not in result:
        result['patches'] = defaultdict(list)
    if p not in result['patches'][file]:
        result['patches'][file].append(p)


def apply_patch(original_txt, patch):
    patched_txt = original_txt[:int(patch['start'])]
    patched_txt += patch['new_string']
    patched_txt += original_txt[int(patch['end']):]
    return patched_txt


def create_diff(original_txt, patched_txt, filename):
    diff = difflib.unified_diff(original_txt.splitlines(False),
                                patched_txt.splitlines(False),
                                fromfile=filename,
                                tofile=filename,
                                lineterm='')

    return '\n'.join(list(diff)) + '\n'
