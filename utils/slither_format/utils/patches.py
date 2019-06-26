import difflib

def create_patch(patches, detector, file_relative, file, start, end, old_str, new_str):
    p = {
        "file": file,
        "detector": detector,
        "start": start,
        "end": end,
        "old_string": old_str,
        "new_string": new_str
    }
    if p not in patches[file_relative]:
        patches[file_relative].append(p)


def apply_patch(original_txt, patch):
    patched_txt = original_txt[:int(patch['start'])]
    patched_txt += patch['new_string']
    patched_txt += original_txt[int(patch['end']):]
    print(patched_txt)
    return patched_txt

def create_diff(original_txt, patched_txt, filename):
    diff = difflib.unified_diff(original_txt.splitlines(False),
                                patched_txt.splitlines(False),
                                fromfile=filename,
                                tofile=filename,
                                lineterm='')

    return '\n'.join(list(diff)) + '\n'
