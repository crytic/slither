
def create_patch(patches, detector, file_relative, file, start, end, old_str, new_str):
    p = {
        "file": file,
        "detector": detector,
        "start": start,
        "end": end,
        "old_string": old_str,
        "new_string": new_str
    }
    if not file_relative in patches:
        patches[file_relative] = []
    if p not in patches[file_relative]:
        patches[file_relative].append(p)