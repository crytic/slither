from ..utils.patches import create_patch


def format(slither, patches, elements):
    for element in elements:
        if element['type'] == "variable":
            _patch(slither, patches,
                   element['source_mapping']['filename_absolute'],
                   element['source_mapping']['filename_relative'],
                   element['source_mapping']['start'])


def _patch(slither, patches, in_file, in_file_relative, modify_loc_start):
    in_file_str = slither.source_code[in_file].encode('utf-8')
    old_str_of_interest = in_file_str[modify_loc_start:]
    old_str = old_str_of_interest.decode('utf-8').partition(';')[0]\
             + old_str_of_interest.decode('utf-8').partition(';')[1]

    create_patch(patches,
                 "unused-state",
                 in_file_relative,
                 in_file,
                 int(modify_loc_start),
                 int(modify_loc_start + len(old_str_of_interest.decode('utf-8').partition(';')[0]) + 1),
                 old_str,
                 "")


