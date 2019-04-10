import sys
import re
from slither.detectors.functions.external_function import ExternalFunction

all_detectors = {
    'external-function':ExternalFunction
}

def slither_format(args, slither):
    detectors_to_run = choose_detectors(args)
    for detector in detectors_to_run:
        slither.register_detector(detector)
    results = []
    detector_results = slither.run_detectors()
    detector_results = [x for x in detector_results if x]  # remove empty results
    detector_results = [item for sublist in detector_results for item in sublist]  # flatten
    results.extend(detector_results)
    apply_detector_results(slither, detector_results)

def apply_detector_results(slither, detector_results):
    patch_count = 0
    for result in detector_results:
        patch_count += 1
        if result['check'] == "external-function":
            format_external_function(slither, result['elements'], patch_count)
        else:
            print("Not Supported Yet.")
            sys.exit(-1)
            
def format_external_function(slither, elements, _patch_count):
    for element in elements:
        print ("Source:"
               + " start: " + str(element['source_mapping']['start'])
               + " length: " + str(element['source_mapping']['length'])
               + " filename: " + element['source_mapping']['filename'])
        Found = False
        for contract in slither.contracts_derived:
            if not Found:
                for function in contract.functions:
                    if contract.name == element['contract']['name'] and function.name == element['name']:
                        print("Contract name: " + contract.name)
                        print("Function name: " + function.name)
                        create_patch(element['source_mapping']['filename'], "public", "external", int(function.parameters_src.split(':')[0]), int(function.returns_src.split(':')[0]), _patch_count)
                        Found = True
                    
def create_patch(_in_file, _match_text, _replace_text, _modify_loc_start, _modify_loc_end, _patch_count):
    print("_modify_loc_start: " + str(_modify_loc_start))
    print("_modify_loc_end: " + str(_modify_loc_end))
    out_file_name = _in_file + ".patch." + str(_patch_count)
    out_file = open(out_file_name, 'w')
    print("Patch file: " + out_file_name)
    with open(_in_file, 'r+') as in_file:
        in_file_str = in_file.read()
        str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
        print("String of interest: " + str_of_interest)
        (str_of_interest, num_repl) = re.subn("public", "extern", str_of_interest, 1)
        if num_repl == 0:
            # No visibility specifier exists; public by default.
            print("public specifier not found.")
            (str_of_interest, num_repl) = re.subn("\)", ") extern", str_of_interest, 1)
        if num_repl != 0:
            out_file_str = in_file_str[:_modify_loc_start] + str_of_interest + in_file_str[_modify_loc_end:]
            out_file.write(out_file_str)
        else:
            print("Error: No public visibility specifier exists. Regex failed to add extern specifier.")
            sys.exit(-1)
        in_file.close()
        out_file.close()
    
def choose_detectors(args):
    # If detectors are specified, run only these ones

    detectors_to_run = []
    
    if args.detectors_to_run == 'all':
        for d in all_detectors:
            detectors_to_run.append(all_detectors[d])
    else:
        for d in args.detectors_to_run.split(','):
            if d in all_detectors:
                detectors_to_run.append(all_detectors[d])
            else:
                raise Exception('Error: {} is not a detector'.format(d))
    return detectors_to_run
