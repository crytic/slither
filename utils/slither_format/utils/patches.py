
def create_patch(patches, detector, file_relative, file, start, end, old_str, new_str):
    patches[file_relative].append({
        "file": file,
        "detector": detector,
        "start": start,
        "end": end,
        "old_string": old_str,
        "new_string": new_str
    })