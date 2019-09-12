import logging
from pathlib import Path
from slither.detectors.variables.unused_state_variables import UnusedStateVars
from slither.detectors.attributes.incorrect_solc import IncorrectSolc
from slither.detectors.attributes.constant_pragma import ConstantPragma
from slither.detectors.naming_convention.naming_convention import NamingConvention
from slither.detectors.functions.external_function import ExternalFunction
from slither.detectors.variables.possible_const_state_variables import ConstCandidateStateVars
from slither.detectors.attributes.const_functions import ConstantFunctions
from .formatters import unused_state, constable_states, pragma, solc_version, \
    external_function, naming_convention, constant_function
from .utils.patches import apply_patch, create_diff
from .exceptions import FormatError, FormatImpossible

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Slither.Format')

all_detectors = {
    'unused-state': UnusedStateVars, 
    'solc-version': IncorrectSolc,
    'pragma': ConstantPragma,
    'naming-convention': NamingConvention,
    'external-function': ExternalFunction,
    'constable-states' : ConstCandidateStateVars,
    'constant-function': ConstantFunctions
}

def slither_format(slither, **kwargs):
    ''''
    Keyword Args:
        detectors_to_run (str): Comma-separated list of detectors, defaults to all
    '''

    detectors_to_run = choose_detectors(kwargs.get('detectors_to_run', 'all'),
                                        kwargs.get('detectors_to_exclude', ''))

    for detector in detectors_to_run:
        slither.register_detector(detector)

    detector_results = slither.run_detectors()
    detector_results = [x for x in detector_results if x]  # remove empty results
    detector_results = [item for sublist in detector_results for item in sublist]  # flatten

    apply_detector_results(slither, detector_results)

    skip_file_generation = kwargs.get('skip-patch-generation', False)

    export = Path('crytic-export', 'patches')

    export.mkdir(parents=True, exist_ok=True)

    counter_result = 0

    for result in detector_results:
        if not 'patches' in result:
            continue
        one_line_description = result["description"].split("\n")[0]

        export_result = Path(export, f'{counter_result}')
        export_result.mkdir(parents=True, exist_ok=True)
        counter_result += 1
        counter = 0

        logger.info(f'Issue: {one_line_description}')
        logger.info(f'Generated: ({export_result})')
        for file in result['patches']:
            original_txt = slither.source_code[file].encode('utf8')
            patched_txt = original_txt
            offset = 0
            patches = result['patches'][file]
            patches.sort(key=lambda x:x['start'])
            if not all(patches[i]['end'] <= patches[i+1]['end'] for i in range(len(patches)-1)):
                logger.info(f'Impossible to generate patch; patches collisions: {patches}')
                continue
            for patch in patches:
                patched_txt, offset = apply_patch(patched_txt, patch, offset)
            diff = create_diff(slither, original_txt, patched_txt, file)
            result['paches_diff'] = diff
            if skip_file_generation:
                continue
            if not diff:
                logger.info(f'Impossible to generate patch; empty {result}')
                continue
            filename = f'fix_{counter}.patch'
            path = Path(export_result, filename)
            logger.info(f'\t- {filename}')
            with open(path, 'w') as f:
                f.write(diff)
            counter += 1


# endregion
###################################################################################
###################################################################################
# region Detectors
###################################################################################
###################################################################################

def choose_detectors(detectors_to_run, detectors_to_exclude):
    # If detectors are specified, run only these ones
    cls_detectors_to_run = []
    exclude = detectors_to_exclude.split(',')
    if detectors_to_run == 'all':
        for d in all_detectors:
            if d in exclude:
                continue
            cls_detectors_to_run.append(all_detectors[d])
    else:
        exclude = detectors_to_exclude.split(',')
        for d in detectors_to_run.split(','):
            if d in all_detectors:
                if d in exclude:
                    continue
                cls_detectors_to_run.append(all_detectors[d])
            else:
                raise Exception('Error: {} is not a detector'.format(d))
    return cls_detectors_to_run

def apply_detector_results(slither, detector_results):
    '''
    Apply slither detector results on contract files to generate patches
    '''
    for result in detector_results:
        try:
            if result['check'] == 'unused-state':
                unused_state.format(slither, result)
            elif result['check'] == 'solc-version':
                solc_version.format(slither, result)
            elif result['check'] == 'pragma':
                pragma.format(slither, result)
            elif result['check'] == 'naming-convention':
                naming_convention.format(slither, result)
            elif result['check'] == 'external-function':
                external_function.format(slither, result)
            elif result['check'] == 'constable-states':
                constable_states.format(slither, result)
            elif result['check'] == 'constant-function':
                constant_function.format(slither, result)
            else:
                raise FormatError(result['check'] + "detector not supported yet.")
        except FormatImpossible as e:
            logger.info(f'\nImpossible to patch:\n\t{result["description"]}\t{e}')


# endregion
###################################################################################
###################################################################################
# region Patch triage (disable)
###################################################################################
###################################################################################

def sort_and_flag_overlapping_patches(patches):
    for file in patches:
        n = len(patches[file])
        for i in range(n):
            for j in range(0, n-i-1):
                # Sort check
                if int(patches[file][j]['start']) > int(patches[file][j+1]['start']):
                    temp = patches[file][j+1]
                    patches[file][j+1] = patches[file][j]
                    patches[file][j] = temp
                # Overlap check
                current = patches[file][j]
                current_start = int(current['start'])
                current_end = int(current['end'])
                next = patches[file][j+1]
                next_start = int(next['start'])
                next_end = int(next['start'])
                if ((current_start >= next_start and current_start <= next_end) or
                    (next_start >= current_start and next_start <= current_end)):
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


# endregion
###################################################################################
###################################################################################
# region Debug functions
###################################################################################
###################################################################################

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
    

