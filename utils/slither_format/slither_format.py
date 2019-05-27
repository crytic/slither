import sys, re, logging, subprocess
from collections import defaultdict
from slither.utils.colors import red, yellow, set_colorization_enabled
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
from .format_unused_state import FormatUnusedState
from .format_solc_version import FormatSolcVersion
from .format_pragma import FormatPragma
from .format_naming_convention import FormatNamingConvention
from .format_external_function import FormatExternalFunction
from .format_constable_states import FormatConstableStates
from .format_constant_function import FormatConstantFunction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Slither.Format')
set_colorization_enabled(True)

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
    sort_and_flag_overlapping_patches(patches)
    prune_overlapping_patches(args, patches)
    if args.verbose_json:
        print_patches_json(number_of_slither_results, patches)
    if args.verbose_test:
        print_patches(number_of_slither_results, patches)    
    generate_patch_files(slither, patches)

def sort_and_flag_overlapping_patches(patches):
    for file in patches:
        n = len(patches[file])
        for i in range(n):
            for j in range (0,n-i-1):
                # Sort check
                if int(patches[file][j]['start']) > int(patches[file][j+1]['start']):
                    temp = patches[file][j+1]
                    patches[file][j+1] = patches[file][j]
                    patches[file][j] = temp
                # Overlap check
                if ((int(patches[file][j]['start']) >= int(patches[file][j+1]['start']) and
                    int(patches[file][j]['start']) <= int(patches[file][j+1]['end'])) or
                    (int(patches[file][j+1]['start']) >= int(patches[file][j]['start']) and
                    int(patches[file][j+1]['start']) <= int(patches[file][j]['end']))):
                    patches[file][j]['overlaps'] = "Yes"
                    patches[file][j+1]['overlaps'] = "Yes"

def is_overlap_patch(args, patch):
    if 'overlaps' in patch:
        if args.verbose_test:
            logger.info("Overlapping patch won't be applied!")
            logger.info("xDetector: " + patch['detector'])
            logger.info("xOld string: " + patch['old_string'].replace("\n",""))
            logger.info("xNew string: " + patch['new_string'].replace("\n",""))
            logger.info("xLocation start: " + str(patch['start']))
            logger.info("xLocation end: " + str(patch['end']))
        return True
    return False

def prune_overlapping_patches(args, patches):
    for file in patches:
        non_overlapping_patches = [patch for patch in patches[file] if not is_overlap_patch(args, patch)]
        patches[file] = non_overlapping_patches
            
def generate_patch_files(slither, patches):
    for file in patches:
        _in_file = file
        if patches[file]:
            in_file_str = slither.source_code[patches[file][0]['file']].encode('utf-8')
        out_file_str = ""
        for i in range(len(patches[file])):
            if i != 0:
                out_file_str += in_file_str[int(patches[file][i-1]['end']):int(patches[file][i]['start'])].decode('utf-8')
            else:
                out_file_str += in_file_str[:int(patches[file][i]['start'])].decode('utf-8')
            out_file_str += patches[file][i]['new_string']
            if (i == (len(patches[file]) - 1)):
                out_file_str += in_file_str[int(patches[file][i]['end']):].decode('utf-8')
        out_file = open(_in_file+".format",'w')
        out_file.write(out_file_str)
        out_file.close()
        patch_file_name = _in_file + ".format.patch"
        outFD = open(patch_file_name,"w")
        p1 = subprocess.Popen(['diff', '-u', _in_file, _in_file+".format"], stdout=outFD)
        p1.wait()
        outFD.close()

def print_patches(number_of_slither_results, patches):
    logger.info("Number of Slither results: " + str(number_of_slither_results))
    number_of_patches = 0
    for file in patches:
        number_of_patches += len(patches[file])
    logger.info("Number of patches: " + str(number_of_patches))
    for file in patches:
        logger.info("Patch file: " + file)
        for patch in patches[file]:
            logger.info("Detector: " + patch['detector'])
            logger.info("Old string: " + patch['old_string'].replace("\n",""))
            logger.info("New string: " + patch['new_string'].replace("\n",""))
            logger.info("Location start: " + str(patch['start']))
            logger.info("Location end: " + str(patch['end']))

def print_patches_json(number_of_slither_results, patches):
    print('{',end='')
    print("\"Number of Slither results\":" + '"' + str(number_of_slither_results) + '",')
    print("\"Number of patchlets\":" + "\"" + str(len(patches)) + "\"", ',')
    print("\"Patchlets\":" + '[')
    for index, file in enumerate(patches):
        if index > 0:
            print(',')
        print('{',end='')
        print("\"Patch file\":" + '"' + file + '",')
        print("\"Number of patches\":" + "\"" + str(len(patches[file])) + "\"", ',')
        print("\"Patches\":" + '[')
        for index, patch in enumerate(patches[file]):
            if index > 0:
                print(',')
            print('{',end='')
            print("\"Detector\":" + '"' + patch['detector'] + '",')
            print("\"Old string\":" + '"' + patch['old_string'].replace("\n","") + '",')
            print("\"New string\":" + '"' + patch['new_string'].replace("\n","") + '",')
            print("\"Location start\":" + '"' + str(patch['start']) + '",')
            print("\"Location end\":" + '"' + str(patch['end']) + '"')
            if 'overlaps' in patch:
                print("\"Overlaps\":" + "Yes")
            print('}',end='')
        print(']',end='')        
        print('}',end='')
    print(']',end='')        
    print('}')
    

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
            logger.error(red("Not Supported Yet."))
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
            
