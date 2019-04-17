import sys, re
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

all_detectors = {
    'unused-state': UnusedStateVars, 
    'solc-version': IncorrectSolc,
    'pragma': ConstantPragma,
    'naming-convention': NamingConvention,
    'external-function': ExternalFunction,
    'constable-states' : ConstCandidateStateVars,
    'constant-function': ConstantFunctions
}

patches = []

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
    print_patches()

def print_patches():
    global patches
    for patch in patches:
        print("Detector: " + patch['detector'])
        print("Old string: " + patch['old_string'])
        print("New string: " + patch['new_string'])
        print("Location start: " + str(patch['start']))
        print("Location end: " + str(patch['end']))
        
def apply_detector_results(slither, detector_results):
    for result in detector_results:
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
    for element in elements:
        create_patch_unused_state(element['source_mapping']['filename'], element['source_mapping']['start'])
    
def format_solc_version(slither, elements):
    print("Not Supported Yet.")
    
def format_pragma(slither, elements):
    print("Not Supported Yet.")
    
def format_naming_convention(slither, elements):
    for element in elements:
        if (element['target'] == "modifier" or element['target'] == "function" or element['target'] == "event"):
            create_patch_naming_convention(slither, element['target'], element['name'], element['contract'], element['source_mapping']['filename'],element['source_mapping']['start'],(element['source_mapping']['start']+element['source_mapping']['length']))
        else:
            create_patch_naming_convention(slither, element['target'], element['name'], element['name'], element['source_mapping']['filename'],element['source_mapping']['start'],(element['source_mapping']['start']+element['source_mapping']['length']))
            
def format_external_function(slither, elements):
    for element in elements:
        Found = False
        for contract in slither.contracts_derived:
            if not Found and contract.name == element['contract']['name']:
                for function in contract.functions:
                    if function.name == element['name']:
                        create_patch_external_function(element['source_mapping']['filename'], "public", "external", int(function.parameters_src.split(':')[0]), int(function.returns_src.split(':')[0]))
                        Found = True
                        break

def format_constable_states(slither, elements):
    for element in elements:
        create_patch_constable_states(element['source_mapping']['filename'], element['name'], "constant " + element['name'], element['source_mapping']['start'], element['source_mapping']['start'] + element['source_mapping']['length'])

def format_constant_function(slither, elements):
    for element in elements:
        if element['type'] != "function":
            # Skip variable elements
            continue
        Found = False
        for contract in slither.contracts_derived:
            if not Found:
                for function in contract.functions:
                    if contract.name == element['contract']['name'] and function.name == element['name']:
                        create_patch_constant_function(element['source_mapping']['filename'], ["view","pure","constant"], "", int(function.parameters_src.split(':')[0]), int(function.returns_src.split(':')[0]))
                        Found = True

def create_patch_naming_convention(_slither, _target, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
    if _target == "contract":
        create_patch_naming_convention_contract_definition(_slither, _name, _in_file, _modify_loc_start, _modify_loc_end)
        create_patch_naming_convention_contract_uses(_slither, _name, _in_file)
    elif _target == "structure":
        pass
    elif _target == "event":
        create_patch_naming_convention_event_definition(_slither, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
        create_patch_naming_convention_event_calls(_slither, _name, _contract_name, _in_file)
    elif _target == "function":
        create_patch_naming_convention_function_definition(_slither, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
        create_patch_naming_convention_function_calls(_slither, _name, _contract_name, _in_file)
    elif _target == "parameter":
        pass
    elif _target == "variable_constant":
        pass
    elif _target == "variable":
        pass
    elif _target == "enum":
        pass
    elif _target == "modifier":
        create_patch_naming_convention_modifier_definition(_slither, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
        create_patch_naming_convention_modifier_uses(_slither, _name, _contract_name, _in_file)
    else:
        print("Unknown naming convention!")
        sys.exit(-1)

def create_patch_naming_convention_contract_definition(_slither, _name, _in_file, _modify_loc_start, _modify_loc_end):
    global patches
    for contract in _slither.contracts_derived:
        if contract.name == _name:
            with open(_in_file, 'r+') as in_file:
                in_file_str = in_file.read()
                old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                m = re.match(r'(.*)'+"contract"+r'(.*)'+_name, old_str_of_interest)
                old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_start+m.span()[1]]
                (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"contract"+r'(.*)'+_name, r'\1'+"contract"+r'\2'+_name.capitalize(), old_str_of_interest, 1)
                if num_repl != 0:
                    patches.append({
                        "detector" : "naming-convention (contract definition)",
                        "start":_modify_loc_start,
                        "end":_modify_loc_start+m.span()[1],
                        "old_string":old_str_of_interest,
                        "new_string":new_str_of_interest
                    })
                    in_file.close()
                else:
                    print("Error: Could not find contract?!")
                    in_file.close()
                    sys.exit(-1)

def create_patch_naming_convention_contract_uses(_slither, _name, _in_file):
    global patches
    for contract in _slither.contracts_derived:
        if contract.name != _name:
            with open(_in_file, 'r+') as in_file:
                in_file_str = in_file.read()
                # Check state variables of contract type
                # To-do: Deep-check aggregate types (struct and mapping)
                svs = contract.variables
                for sv in svs:
                    if (str(sv.type) == _name):
                        old_str_of_interest = in_file_str[contract.get_source_var_declaration(sv.name)['start']:(contract.get_source_var_declaration(sv.name)['start']+contract.get_source_var_declaration(sv.name)['length'])]
                        (new_str_of_interest, num_repl) = re.subn(_name, _name.capitalize(),old_str_of_interest, 1)
                        patches.append({
                            "detector" : "naming-convention (contract state variable)",
                            "start" : contract.get_source_var_declaration(sv.name)['start'],
                            "end" : contract.get_source_var_declaration(sv.name)['start'] + contract.get_source_var_declaration(sv.name)['length'],
                            "old_string" : old_str_of_interest,
                            "new_string" : new_str_of_interest
                        })
                # Check function+modifier locals+parameters+returns
                # To-do: Deep-check aggregate types (struct and mapping)
                fms = contract.functions + contract.modifiers
                for fm in fms:
                    for v in fm.variables:
                        if (str(v.type) == _name):
                            old_str_of_interest = in_file_str[fm.get_source_var_declaration(v.name)['start']:(fm.get_source_var_declaration(v.name)['start']+fm.get_source_var_declaration(v.name)['length'])]
                            (new_str_of_interest, num_repl) = re.subn(_name, _name.capitalize(),old_str_of_interest, 1)
                            patches.append({
                                "detector" : "naming-convention (contract function variable)",
                                "start" : fm.get_source_var_declaration(v.name)['start'],
                                "end" : fm.get_source_var_declaration(v.name)['start'] + fm.get_source_var_declaration(v.name)['length'],
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                        })
                # To-do: Check any other place where contract type is used
        else:
            # Ignore contract definition
            continue

def create_patch_naming_convention_modifier_definition(_slither, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
    global patches
    for contract in _slither.contracts_derived:
        if contract.name == _contract_name:
            for modifier in contract.modifiers:
                if modifier.name == _name:
                    with open(_in_file, 'r+') as in_file:
                        in_file_str = in_file.read()
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                        m = re.match(r'(.*)'+"modifier"+r'(.*)'+_name, old_str_of_interest)
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_start+m.span()[1]]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"modifier"+r'(.*)'+_name, r'\1'+"modifier"+r'\2'+_name[0].lower()+_name[1:], old_str_of_interest, 1)
                if num_repl != 0:
                    patches.append({
                        "detector" : "naming-convention (modifier definition)",
                        "start" : _modify_loc_start,
                        "end" : _modify_loc_start+m.span()[1],
                        "old_string" : old_str_of_interest,
                        "new_string" : new_str_of_interest
                    })
                    in_file.close()
                else:
                    print("Error: Could not find modifier?!")
                    in_file.close()
                    sys.exit(-1)

def create_patch_naming_convention_modifier_uses(_slither, _name, _contract_name, _in_file):
    global patches
    for contract in _slither.contracts_derived:
        if contract.name == _contract_name:
            for function in contract.functions:
                for m  in function.modifiers:
                    if (m.name == _name):
                        with open(_in_file, 'r+') as in_file:
                            in_file_str = in_file.read()
                            old_str_of_interest = in_file_str[int(function.parameters_src.split(':')[0]):int(function.returns_src.split(':')[0])]
                            (new_str_of_interest, num_repl) = re.subn(_name, _name[0].lower()+_name[1:],old_str_of_interest,1)
                            if num_repl != 0:
                                patches.append({
                                    "detector" : "naming-convention (modifier uses)",
                                    "start" : int(function.parameters_src.split(':')[0]),
                                    "end" : int(function.returns_src.split(':')[0]),
                                    "old_string" : old_str_of_interest,
                                    "new_string" : new_str_of_interest
                                })
                                in_file.close()
                            else:
                                print("Error: Could not find modifier name?!")
                                in_file.close()
                                sys.exit(-1)

def create_patch_naming_convention_function_definition(_slither, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
    # To-do Match on function full_name and not simply name to distinguish functions with same names but diff parameters
    global patches
    for contract in _slither.contracts_derived:
        if contract.name == _contract_name:
            for function in contract.functions:
                if function.name == _name:
                    with open(_in_file, 'r+') as in_file:
                        in_file_str = in_file.read()
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                        m = re.match(r'(.*)'+"function"+r'(.*)'+_name, old_str_of_interest)
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_start+m.span()[1]]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"function"+r'(.*)'+_name, r'\1'+"function"+r'\2'+_name[0].lower()+_name[1:], old_str_of_interest, 1)
                        if num_repl != 0:
                            patches.append({
                                "detector" : "naming-convention (function definition)",
                                "start" : _modify_loc_start,
                                "end" : _modify_loc_start+m.span()[1],
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            })
                            in_file.close()
                        else:
                            print("Error: Could not find function?!")
                            in_file.close()
                            sys.exit(-1)

def create_patch_naming_convention_function_calls(_slither, _name, _contract_name, _in_file):
    # To-do Match on function full_name and not simply name to distinguish functions with same names but diff parameters
    global patches
    for contract in _slither.contracts_derived:
        for function in contract.functions:
            for node in function.nodes:
                # To-do: Handle function calls of other contracts e.g. c.foo()
                for call in node.internal_calls_as_expressions:
                    if (str(call.called) == _name):
                        with open(_in_file, 'r+') as in_file:
                            in_file_str = in_file.read()
                            old_str_of_interest = in_file_str[int(call.src.split(':')[0]):int(call.src.split(':')[0])+int(call.src.split(':')[1])]
                            patches.append({
                                "detector" : "naming-convention (function calls)",
                                "start" : call.src.split(':')[0],
                                "end" : int(call.src.split(':')[0]) + int(call.src.split(':')[1]),
                                "old_string" : old_str_of_interest,
                                "new_string" : old_str_of_interest[0].lower()+old_str_of_interest[1:]
                            })
                            in_file.close()

def create_patch_naming_convention_event_definition(_slither, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
    global patches
    for contract in _slither.contracts_derived:
        if contract.name == _contract_name:
            for event in contract.events:
                if event.full_name == _name:
                    event_name = _name.split('(')[0]
                    with open(_in_file, 'r+') as in_file:
                        in_file_str = in_file.read()
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"event"+r'(.*)'+event_name, r'\1'+"event"+r'\2'+event_name[0].capitalize()+event_name[1:], old_str_of_interest, 1)
                        if num_repl != 0:
                            patches.append({
                                "detector" : "naming-convention (event definition)",
                                "start" : _modify_loc_start,
                                "end" : _modify_loc_end,
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            })
                            in_file.close()
                        else:
                            print("Error: Could not find event?!")
                            in_file.close()
                            sys.exit(-1)

def create_patch_naming_convention_event_calls(_slither, _name, _contract_name, _in_file):
    # To-do Match on event _name and not simply event_name to distinguish events with same names but diff parameters    
    global patches
    event_name = _name.split('(')[0]
    for contract in _slither.contracts_derived:
        for function in contract.functions:
            for node in function.nodes:
                for call in node.internal_calls_as_expressions:
                    if (str(call.called) == event_name):
                        with open(_in_file, 'r+') as in_file:
                            in_file_str = in_file.read()
                            old_str_of_interest = in_file_str[int(call.src.split(':')[0]):int(call.src.split(':')[0])+int(call.src.split(':')[1])]
                            patches.append({
                                "detector" : "naming-convention (event calls)",
                                "start" : call.src.split(':')[0],
                                "end" : int(call.src.split(':')[0]) + int(call.src.split(':')[1]),
                                "old_string" : old_str_of_interest,
                                "new_string" : old_str_of_interest[0].capitalize()+old_str_of_interest[1:]
                            })
                            in_file.close()

def create_patch_unused_state(_in_file, _modify_loc_start):
    with open(_in_file, 'r+') as in_file:
        in_file_str = in_file.read()
        old_str_of_interest = in_file_str[_modify_loc_start:]
        patches.append({
            "detector" : "unused-state",
            "start" : _modify_loc_start,
            "end" : _modify_loc_start + len(old_str_of_interest.partition(';')[0]),
            "old_string" : old_str_of_interest.partition(';')[0] + old_str_of_interest.partition(';')[1],
            "new_string" : ""
        })
        in_file.close()

def create_patch_external_function(_in_file, _match_text, _replace_text, _modify_loc_start, _modify_loc_end):
    with open(_in_file, 'r+') as in_file:
        in_file_str = in_file.read()
        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
        (new_str_of_interest, num_repl) = re.subn(_match_text, _replace_text, old_str_of_interest, 1)
        if num_repl == 0:
            # No visibility specifier exists; public by default.
            (new_str_of_interest, num_repl) = re.subn("\)", ") extern", old_str_of_interest, 1)
        if num_repl != 0:
            patches.append({
                "detector" : "external-function",
                "start" : _modify_loc_start,
                "end" : _modify_loc_start + len(new_str_of_interest),
                "old_string" : old_str_of_interest,
                "new_string" : new_str_of_interest
            })
            in_file.close()
        else:
            print("Error: No public visibility specifier exists. Regex failed to add extern specifier!")
            in_file.close()
            sys.exit(-1)

def create_patch_constant_function(_detector, _in_file, _match_text, _replace_text, _modify_loc_start, _modify_loc_end):
    with open(_in_file, 'r+') as in_file:
        in_file_str = in_file.read()
        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
        for _match_text_item in _match_text:
            (new_str_of_interest, num_repl) = re.subn(_match_text_item, _replace_text, old_str_of_interest, 1)
            if num_repl != 0:
                break
        if num_repl != 0:
            patches.append({
                "detector" : "constant-function",
                "start" : _modify_loc_start,
                "end" : _modify_loc_start + len(new_str_of_interest),
                "old_string" : old_str_of_interest,
                "new_string" : new_str_of_interest
            })
            in_file.close()
        else:
            print("Error: No view/pure/constant specifier exists. Regex failed to remove specifier!")
            in_file.close()
            sys.exit(-1)

def create_patch_constable_states(_in_file, _match_text, _replace_text, _modify_loc_start, _modify_loc_end):
    with open(_in_file, 'r+') as in_file:
        in_file_str = in_file.read()
        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
        (new_str_of_interest, num_repl) = re.subn(_match_text, _replace_text, old_str_of_interest, 1)
        if num_repl != 0:
            patches.append({
                "detector" : "constable-states",
                "start" : _modify_loc_start,
                "end" : _modify_loc_start + len(new_str_of_interest),
                "old_string" : old_str_of_interest,
                "new_string" : new_str_of_interest
            })
            in_file.close()
        else:
            print("Error: State variable not found?!")
            in_file.close()
            sys.exit(-1)

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
