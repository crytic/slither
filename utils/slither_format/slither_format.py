import sys
import re
from slither.detectors.variables.unused_state_variables import UnusedStateVars
from slither.detectors.attributes.incorrect_solc import IncorrectSolc
from slither.detectors.attributes.constant_pragma import ConstantPragma
from slither.detectors.naming_convention.naming_convention import NamingConvention
from slither.detectors.functions.external_function import ExternalFunction
from slither.detectors.variables.possible_const_state_variables import ConstCandidateStateVars
from slither.detectors.attributes.const_functions import ConstantFunctions

all_detectors = {
    'unused-state': UnusedStateVars, 
    'solc-version': IncorrectSolc,
    'pragma': ConstantPragma,
    'naming-convention': NamingConvention,
    'external-function': ExternalFunction,
    'constable-states' : ConstCandidateStateVars,
    'constant-function': ConstantFunctions
}

patch_count = 0

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
    for result in detector_results:
        print("Result: " + str(result))
        if result['check'] == 'unused-state':
            format_unused_state(slither, result['elements'])
        elif result['check'] == 'solc-version':
            format_solc_version(slither, result['elements'])
        elif result['check'] == 'pragma':
            format_pragma(slither, result['elements'])
        elif result['check'] == 'naming-convention':
            format_naming_convention(slither, result['elements'])
        elif result['check'] == 'external-function':
            format_external_function(slither, result['elements'])
        elif result['check'] == 'constable-states':
            format_constable_states(slither, result['elements'])
        elif result['check'] == 'constant-function':
            format_constant_function(slither, result['elements'])
        else:
            print("Not Supported Yet.")
            sys.exit(-1)

def format_unused_state(slither, elements):
    global patch_count
    for element in elements:
        patch_count += 1
        print ("State variable:"
               + " name: " + str(element['name'])
               + " start: " + str(element['source_mapping']['start'])
               + " length: " + str(element['source_mapping']['length'])
               + " filename: " + element['source_mapping']['filename'])
        create_patch_unused_state("unused-state", element['source_mapping']['filename'], element['source_mapping']['start'], patch_count)
    
def format_solc_version(slither, elements):
    print("Not Supported Yet.")
    
def format_pragma(slither, elements):
    print("Not Supported Yet.")
    
def format_naming_convention(slither, elements):
    print("Not Supported Yet.")
            
def format_external_function(slither, elements):
    global patch_count
    for element in elements:
        patch_count += 1
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
                        create_patch("external-function", element['source_mapping']['filename'], "public", "external", int(function.parameters_src.split(':')[0]), int(function.returns_src.split(':')[0]), patch_count)
                        Found = True

def format_constable_states(slither, elements):
    global patch_count
    for element in elements:
        patch_count += 1
        print ("State variable:"
               + " name: " + str(element['name'])
               + " start: " + str(element['source_mapping']['start'])
               + " length: " + str(element['source_mapping']['length'])
               + " filename: " + element['source_mapping']['filename'])
        create_patch("constable-states", element['source_mapping']['filename'], element['name'], "constant " + element['name'], element['source_mapping']['start'], element['source_mapping']['start'] + element['source_mapping']['length'], patch_count)

def format_constant_function(slither, elements):
    global patch_count
    for element in elements:
        if element['type'] != "function":
            # Skip variable elements
            continue
        patch_count += 1
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
                        create_patch("constant-function", element['source_mapping']['filename'], ["view","pure","constant"], "", int(function.parameters_src.split(':')[0]), int(function.returns_src.split(':')[0]), patch_count)
                        Found = True

def create_patch_unused_state(_detector, _in_file, _modify_loc_start, _patch_count):
    out_file_name = _in_file + ".patch." + str(_patch_count)
    out_file = open(out_file_name, 'w')
    print("Patch file: " + out_file_name)
    with open(_in_file, 'r+') as in_file:
        in_file_str = in_file.read()
        str_of_interest = in_file_str[_modify_loc_start:]
        str_of_interest = str_of_interest.partition(';')[2]
        out_file_str = in_file_str[:_modify_loc_start] + str_of_interest
        out_file.write(out_file_str)
        in_file.close()
        out_file.close()

def create_patch(_detector, _in_file, _match_text, _replace_text, _modify_loc_start, _modify_loc_end, _patch_count):
    print("_modify_loc_start: " + str(_modify_loc_start))
    print("_modify_loc_end: " + str(_modify_loc_end))
    out_file_name = _in_file + ".patch." + str(_patch_count)
    out_file = open(out_file_name, 'w')
    print("Patch file: " + out_file_name)
    with open(_in_file, 'r+') as in_file:
        in_file_str = in_file.read()
        if not isinstance(_match_text, list):
            if _detector == "unused-state":
                str_of_interest = in_file_str[_modify_loc_start:]
                str_of_interest = str_of_interest.partition(";")[0] + ";"
                print("String of interest: " + str_of_interest)
                print("Replace text: " + _replace_text)
                (str_of_interest, num_repl) = re.subn(str_of_interest, _replace_text, str_of_interest, 1)
                print("String of interest after replacement: " + str_of_interest)
            else:
                str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                print("String of interest: " + str_of_interest)
                (str_of_interest, num_repl) = re.subn(_match_text, _replace_text, str_of_interest, 1)
        else:
            str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
            print("String of interest: " + str_of_interest)
            for _match_text_item in _match_text:
                (str_of_interest, num_repl) = re.subn(_match_text_item, _replace_text, str_of_interest, 1)
                if num_repl != 0:
                    break
        if num_repl == 0 and _detector == "external-function":
            # No visibility specifier exists; public by default.
            print("public specifier not found.")
            (str_of_interest, num_repl) = re.subn("\)", ") extern", str_of_interest, 1)
        if num_repl != 0:
            out_file_str = in_file_str[:_modify_loc_start] + str_of_interest + in_file_str[_modify_loc_end:]
            out_file.write(out_file_str)
        else:
            if _detector == "external-function":
                print("Error: No public visibility specifier exists. Regex failed to add extern specifier.")
            elif _detector == "constable-states":
                print("Error: State variable not found?!")
            elif _detector == "constant-function":
                print("Error: No view/pure/constant specifier exists. Regex failed to remove specifier.")
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
