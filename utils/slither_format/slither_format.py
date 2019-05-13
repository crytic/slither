import sys, re
from collections import defaultdict
from slither.detectors.variables.unused_state_variables import UnusedStateVars
from slither.detectors.attributes.incorrect_solc import IncorrectSolc
from slither.detectors.attributes.constant_pragma import ConstantPragma
from slither.detectors.naming_convention.naming_convention import NamingConvention
from slither.detectors.functions.external_function import ExternalFunction
from slither.detectors.variables.possible_const_state_variables import ConstCandidateStateVars
from slither.detectors.attributes.const_functions import ConstantFunctions
from slither.slithir.operations import InternalCall
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.expression import Expression
from slither.core.expressions.identifier import Identifier
from slither_format.format_unused_state import FormatUnusedState
from slither_format.format_solc_version import FormatSolcVersion
from slither_format.format_pragma import FormatPragma
from slither_format.format_naming_convention import FormatNamingConvention
from slither_format.format_external_function import FormatExternalFunction
from slither_format.format_constable_states import FormatConstableStates
from slither_format.format_constant_function import FormatConstantFunction

all_detectors = {
    'unused-state': UnusedStateVars, 
    'solc-version': IncorrectSolc,
    'pragma': ConstantPragma,
    'naming-convention': NamingConvention,
    'external-function': ExternalFunction,
    'constable-states' : ConstCandidateStateVars,
    'constant-function': ConstantFunctions
}

def slither_format(args, slither):
    patches = defaultdict(list)
    detectors_to_run = choose_detectors(args)
    for detector in detectors_to_run:
        slither.register_detector(detector)
    results = []
    detector_results = slither.run_detectors()
    detector_results = [x for x in detector_results if x]  # remove empty results
    detector_results = [item for sublist in detector_results for item in sublist]  # flatten
    results.extend(detector_results)
    number_of_slither_results = get_number_of_slither_results(detector_results)
    apply_detector_results(slither, patches, detector_results)
    sort_patches(patches)
    if args.verbose:
        print("Number of Slither results: " + str(number_of_slither_results))
        print_patches(patches)
    apply_patches(slither, patches)

def sort_patches(patches):
    for file in patches:
        n = len(patches[file])
        for i in range(n):
            for j in range (0,n-i-1):
                if int(patches[file][j]['start']) >= int(patches[file][j+1]['end']):
                    temp = patches[file][j+1]
                    patches[file][j+1] = patches[file][j]
                    patches[file][j] = temp

def apply_patches(slither, patches):
    for file in patches:
        _in_file = file
        in_file_str = slither.source_code[_in_file]
        out_file_str = ""
        for i in range(len(patches[file])):
            if i != 0:
                out_file_str += in_file_str[int(patches[file][i-1]['end']):int(patches[file][i]['start'])]
            else:
                out_file_str += in_file_str[:int(patches[file][i]['start'])]
            out_file_str += patches[file][i]['new_string']
        out_file_str += in_file_str[int(patches[file][i]['end']):]
        out_file = open(_in_file+".format",'w')
        out_file.write(out_file_str)
        out_file.close()

def print_patches(patches):
    number_of_patches = 0
    for file in patches:
        number_of_patches += len(patches[file])
    print("Number of patches: " + str(number_of_patches))
    for file in patches:
        print("Patch file: " + file)
        for patch in patches[file]:
            print("Detector: " + patch['detector'])
            print("Old string: " + patch['old_string'].replace("\n",""))
            print("New string: " + patch['new_string'].replace("\n",""))
            print("Location start: " + str(patch['start']))
            print("Location end: " + str(patch['end']))

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

def apply_detector_results(slither, patches, detector_results):
    for result in detector_results:
        if result['check'] == 'unused-state':
            FormatUnusedState.format(slither, patches, result['elements'])
        elif result['check'] == 'solc-version':
            FormatSolcVersion.format(slither, patches, result['elements'])
        elif result['check'] == 'pragma':
            FormatPragma.format(slither, patches, result['elements'])
        elif result['check'] == 'naming-convention':
            FormatNamingConvention.format(slither, patches, result['elements'])
        elif result['check'] == 'external-function':
            FormatExternalFunction.format(slither, patches, result['elements'])
        elif result['check'] == 'constable-states':
            FormatConstableStates.format(slither, patches, result['elements'])
        elif result['check'] == 'constant-function':
            FormatConstantFunction.format(slither, patches, result['elements'])
        else:
            print("Not Supported Yet.")
            sys.exit(-1)

def get_number_of_slither_results (detector_results):
    number_of_slither_results = 0
    for result in detector_results:
        for elem in result['elements']:
            if (result['check'] == 'constant-function' and elem['type'] != "function"):
                continue
            if (result['check'] == 'unused-state' and elem['type'] != "variable"):
                continue
            number_of_slither_results += 1
    return number_of_slither_results
            
