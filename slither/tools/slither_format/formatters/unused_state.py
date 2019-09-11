from ..utils.patches import create_patch


def format(slither, result):
    elements = result['elements']
    for element in elements:
        if element['type'] == "variable":
            _patch(slither,
                   result,
                   element['source_mapping']['filename_absolute'],
                   element['source_mapping']['start'])


def _patch(slither, result, in_file, modify_loc_start):
    in_file_str = slither.source_code[in_file].encode('utf8')
    old_str_of_interest = in_file_str[modify_loc_start:]
    old_str = old_str_of_interest.decode('utf-8').partition(';')[0]\
             + old_str_of_interest.decode('utf-8').partition(';')[1]

    create_patch(result,
                 in_file,
                 int(modify_loc_start),
                 # Remove the entire declaration until the semicolon
                 int(modify_loc_start + len(old_str_of_interest.decode('utf-8').partition(';')[0]) + 1),
                 old_str,
                 "")


