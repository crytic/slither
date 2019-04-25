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
from slither.core.expressions.identifier import Identifier

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
    number_of_slither_results = get_number_of_slither_results(detector_results)
    apply_detector_results(slither, detector_results)
    sort_patches()
    if args.verbose:
        print("Number of Slither results: " + str(number_of_slither_results))
        print_patches()
    apply_patches()

def get_number_of_slither_results (detector_results):
    number_of_slither_results = 0
    for result in detector_results:
        for elem in result['elements']:
            number_of_slither_results += 1
    return number_of_slither_results
            
def sort_patches():
    n = len(patches)
    for i in range(n):
        for j in range (0,n-i-1):
            if int(patches[j]['start']) >= int(patches[j+1]['end']):
                temp = patches[j+1]
                patches[j+1] = patches[j]
                patches[j] = temp
    
def print_patches():
    global patches
    print("Number of patches: " + str(len(patches)))
    for patch in patches:
        print("Detector: " + patch['detector'])
        print("Old string: " + patch['old_string'].replace("\n",""))
        print("New string: " + patch['new_string'].replace("\n",""))
        print("Location start: " + str(patch['start']))
        print("Location end: " + str(patch['end']))
        print("Patch file: " + str(patch['patch_file']))

def apply_patches():
    global patches
    # Assuming all patches are applicable to the same file for now
    # To-do Classify patches according to patch_file
    _in_file = patches[0]['patch_file']
    with open(_in_file, 'r+') as in_file:
        in_file_str = in_file.read()
        out_file_str = ""
        for i in range(len(patches)):
            if patches[i]['patch_file'] != _in_file:
                continue
            if i != 0:
                out_file_str += in_file_str[int(patches[i-1]['end']):int(patches[i]['start'])]
            else:
                out_file_str += in_file_str[:int(patches[i]['start'])]
            out_file_str += patches[i]['new_string']
        out_file_str += in_file_str[int(patches[i]['end']):]
        out_file = open(_in_file+".format",'w')
        out_file.write(out_file_str)
        out_file.close()
    
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
    # To-do: Determine which solc version to replace with
    # If < 0.4.24 replace with 0.4.25?
    # If > 0.5.0 replace with the latest 0.5.x?
    solc_version_replace = "pragma solidity 0.4.25;"
    for element in elements:
        create_patch_solc_version(element['source_mapping']['filename'], solc_version_replace, element['source_mapping']['start'], element['source_mapping']['start'] + element['source_mapping']['length'])

def format_pragma(slither, elements):
    versions_used = []
    for element in elements:
        versions_used.append(element['expression'])
    # To-do Determine which version to replace with
    # The more recent of the two? What if they are the older deprecated versions? Replace it with the latest?
    # Impact of upgrading and compatibility? Cannot upgrade across breaking versions e.g. 0.4.x to 0.5.x.
    solc_version_replace = "^0.4.25"
    pragma = "pragma solidity " + solc_version_replace + ";"
    for element in elements:
        create_patch_different_pragma(element['source_mapping']['filename'], pragma, element['source_mapping']['start'], element['source_mapping']['start'] + element['source_mapping']['length'])
    
def format_naming_convention(slither, elements):
    for element in elements:
        if (element['target'] == "parameter"):
            create_patch_naming_convention(slither, element['target'], element['name'], element['function'], element['contract'], element['source_mapping']['filename'],element['source_mapping']['start'],(element['source_mapping']['start']+element['source_mapping']['length']))
        elif (element['target'] == "modifier" or element['target'] == "function" or element['target'] == "event" or element['target'] == "variable" or element['target'] == "variable_constant" or element['target'] == "enum" or element['target'] == "structure"):
            create_patch_naming_convention(slither, element['target'], element['name'], element['name'], element['contract'], element['source_mapping']['filename'],element['source_mapping']['start'],(element['source_mapping']['start']+element['source_mapping']['length']))
        else:
            create_patch_naming_convention(slither, element['target'], element['name'], element['name'], element['name'], element['source_mapping']['filename'],element['source_mapping']['start'],(element['source_mapping']['start']+element['source_mapping']['length']))
            
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

def create_patch_naming_convention(_slither, _target, _name, _function_name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
    if _target == "contract":
        create_patch_naming_convention_contract_definition(_slither, _name, _in_file, _modify_loc_start, _modify_loc_end)
        create_patch_naming_convention_contract_uses(_slither, _name, _in_file)
    elif _target == "structure":
        create_patch_naming_convention_struct_definition(_slither, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
        create_patch_naming_convention_struct_uses(_slither, _name, _contract_name, _in_file)
    elif _target == "event":
        create_patch_naming_convention_event_definition(_slither, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
        create_patch_naming_convention_event_calls(_slither, _name, _contract_name, _in_file)
    elif _target == "function":
        create_patch_naming_convention_function_definition(_slither, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
        create_patch_naming_convention_function_calls(_slither, _name, _contract_name, _in_file)
    elif _target == "parameter":
        create_patch_naming_convention_parameter_declaration(_slither, _name, _function_name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
        create_patch_naming_convention_parameter_uses(_slither, _name, _function_name, _contract_name, _in_file)
    elif _target == "variable_constant" or _target == "variable":
        create_patch_naming_convention_state_variable_declaration(_slither, _target, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
        create_patch_naming_convention_state_variable_uses(_slither, _target, _name, _contract_name, _in_file)
    elif _target == "enum":
        create_patch_naming_convention_enum_definition(_slither, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
        create_patch_naming_convention_enum_uses(_slither, _name, _contract_name, _in_file)
    elif _target == "modifier":
        create_patch_naming_convention_modifier_definition(_slither, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
        create_patch_naming_convention_modifier_uses(_slither, _name, _contract_name, _in_file)
    else:
        print("Unknown naming convention! " + _target)
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
                        "new_string":new_str_of_interest,
                        "patch_file" : _in_file
                    })
                else:
                    print("Error: Could not find contract?!")
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
                            "new_string" : new_str_of_interest,
                            "patch_file" : _in_file
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
                                "new_string" : new_str_of_interest,
                                "patch_file" : _in_file
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
                                "new_string" : new_str_of_interest,
                                "patch_file" : _in_file
                            })
                        else:
                            print("Error: Could not find modifier?!")
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
                                    "new_string" : new_str_of_interest,
                                    "patch_file" : _in_file
                                })
                            else:
                                print("Error: Could not find modifier name?!")
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
                                "new_string" : new_str_of_interest,
                                "patch_file" : _in_file
                            })
                        else:
                            print("Error: Could not find function?!")
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
                                "new_string" : old_str_of_interest[0].lower()+old_str_of_interest[1:],
                                "patch_file" : _in_file
                            })

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
                                "new_string" : new_str_of_interest,
                                "patch_file" : _in_file
                            })
                        else:
                            print("Error: Could not find event?!")
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
                                "new_string" : old_str_of_interest[0].capitalize()+old_str_of_interest[1:],
                                "patch_file" : _in_file
                            })

def create_patch_naming_convention_parameter_declaration(_slither, _name, _function_name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
    global patches
    for contract in _slither.contracts_derived:
        if contract.name == _contract_name:
            for function in contract.functions:
                if function.name == _function_name:
                    with open(_in_file, 'r+') as in_file:
                        in_file_str = in_file.read()
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                        if(_name[0] == '_'):
                            (new_str_of_interest, num_repl) = re.subn(r'(.*)'+_name+r'(.*)', r'\1'+_name[0]+_name[1].upper()+_name[2:]+r'\2', old_str_of_interest, 1)
                        else:
                            (new_str_of_interest, num_repl) = re.subn(r'(.*)'+_name+r'(.*)', r'\1'+'_'+_name[0].upper()+_name[1:]+r'\2', old_str_of_interest, 1)
                        if num_repl != 0:
                            patches.append({
                                "detector" : "naming-convention (parameter declaration)",
                                "start" : _modify_loc_start,
                                "end" : _modify_loc_end,
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest,
                                "patch_file" : _in_file
                            })
                        else:
                            print("Error: Could not find parameter?!")
                            sys.exit(-1)

def create_patch_naming_convention_parameter_uses(_slither, _name, _function_name, _contract_name, _in_file):
    global patches
    for contract in _slither.contracts_derived:
        if (contract.name == _contract_name):
            for function in contract.functions:
                if (function.name == _function_name):
                    for node in function.nodes:
                        vars = node._expression_vars_written + node._expression_vars_read
                        for v in vars:
                            if isinstance(v, Identifier) and str(v) == _name and [str(lv) for lv in (node._local_vars_read+node._local_vars_written) if str(lv) == _name]:
                                modify_loc_start = int(v.src.split(':')[0])
                                modify_loc_end = int(v.src.split(':')[0]) + int(v.src.split(':')[1])
                                with open(_in_file, 'r+') as in_file:
                                    in_file_str = in_file.read()
                                    old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                                    if(_name[0] == '_'):
                                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+_name+r'(.*)', r'\1'+_name[0]+_name[1].upper()+_name[2:]+r'\2', old_str_of_interest, 1)
                                    else:
                                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+_name+r'(.*)', r'\1'+'_'+_name[0].upper()+_name[1:]+r'\2', old_str_of_interest, 1)
                                    if num_repl != 0:
                                        patches.append({
                                            "detector" : "naming-convention (parameter uses)",
                                            "start" : modify_loc_start,
                                            "end" : modify_loc_end,
                                            "old_string" : old_str_of_interest,
                                            "new_string" : new_str_of_interest,
                                            "patch_file" : _in_file
                                        })
                                    else:
                                        print("Error: Could not find parameter?!")
                                        sys.exit(-1)

def create_patch_naming_convention_state_variable_declaration(_slither, _target, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
    global patches
    for contract in _slither.contracts_derived:
        if (contract.name == _contract_name):
            for var in contract.state_variables:
                if (var.name == _name):
                    with open(_in_file, 'r+') as in_file:
                        in_file_str = in_file.read()
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                        m = re.search(_name, old_str_of_interest)
                        if (_target == "variable_constant"):
                            new_string = old_str_of_interest[m.span()[0]:m.span()[1]].upper()
                        else:
                            # To-do: Determine the new name for non-constant state variables
                            new_string = old_str_of_interest[m.span()[0]:m.span()[1]]
                        patches.append({
                            "detector" : "naming-convention (state variable declaration)",
                            "start" : _modify_loc_start+m.span()[0],
                            "end" : _modify_loc_start+m.span()[1],
                            "old_string" : old_str_of_interest[m.span()[0]:m.span()[1]],
                            "new_string" : new_string,
                            "patch_file" : _in_file
                        })
                        
def create_patch_naming_convention_state_variable_uses(_slither, _target, _name, _contract_name, _in_file):
    # To-do: Check cross-contract state variable uses
    global patches
    for contract in _slither.contracts_derived:
        if (contract.name == _contract_name):
            fms = contract.functions + contract.modifiers
            for fm in fms:
                for node in fm.nodes:
                    vars = node._expression_vars_written + node._expression_vars_read
                    for v in vars:
                        if isinstance(v, Identifier) and str(v) == _name and [str(sv) for sv in (node._state_vars_read+node._state_vars_written) if str(sv) == _name]:
                            modify_loc_start = int(v.src.split(':')[0])
                            modify_loc_end = int(v.src.split(':')[0]) + int(v.src.split(':')[1])
                            with open(_in_file, 'r+') as in_file:
                                in_file_str = in_file.read()
                                old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                                if (_target == "variable_constant"):
                                    new_str_of_interest = old_str_of_interest.upper()
                                else:
                                    # To-do: Determine the new name for non-constant state variables
                                    new_str_of_interest = old_str_of_interest
                                patches.append({
                                    "detector" : "naming-convention (state variable uses)",
                                    "start" : modify_loc_start,
                                    "end" : modify_loc_end,
                                    "old_string" : old_str_of_interest,
                                    "new_string" : new_str_of_interest,
                                    "patch_file" : _in_file
                                })

def create_patch_naming_convention_enum_definition(_slither, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
    global patches
    for contract in _slither.contracts_derived:
        if (contract.name == _contract_name):
            for enum in contract.enums:
                if (enum.name == _name):
                    with open(_in_file, 'r+') as in_file:
                        in_file_str = in_file.read()
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"enum"+r'(.*)'+_name, r'\1'+"enum"+r'\2'+_name[0].capitalize()+_name[1:], old_str_of_interest, 1)
                        if num_repl != 0:
                            patches.append({
                                "detector" : "naming-convention (enum definition)",
                                "start" : _modify_loc_start,
                                "end" : _modify_loc_end,
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest,
                                "patch_file" : _in_file
                            })
                        else:
                            print("Error: Could not find enum?!")
                            sys.exit(-1)

def create_patch_naming_convention_enum_uses(_slither, _name, _contract_name, _in_file):
    global patches
    for contract in _slither.contracts_derived:
        with open(_in_file, 'r+') as in_file:
            in_file_str = in_file.read()
            # Check state variable declarations of enum type
            # To-do: Deep-check aggregate types (struct and mapping)
            svs = contract.variables
            for sv in svs:
                if (str(sv.type) == _contract_name + "." + _name):
                    old_str_of_interest = in_file_str[contract.get_source_var_declaration(sv.name)['start']:(contract.get_source_var_declaration(sv.name)['start']+contract.get_source_var_declaration(sv.name)['length'])]
                    (new_str_of_interest, num_repl) = re.subn(_name, _name.capitalize(),old_str_of_interest, 1)
                    patches.append({
                        "detector" : "naming-convention (enum use)",
                        "start" : contract.get_source_var_declaration(sv.name)['start'],
                        "end" : contract.get_source_var_declaration(sv.name)['start'] + contract.get_source_var_declaration(sv.name)['length'],
                        "old_string" : old_str_of_interest,
                        "new_string" : new_str_of_interest,
                        "patch_file" : _in_file
                    })
            # Check function+modifier locals+parameters+returns
            # To-do: Deep-check aggregate types (struct and mapping)
            fms = contract.functions + contract.modifiers
            for fm in fms:
                # Enum declarations
                for v in fm.variables:
                    if (str(v.type) == _contract_name + "." + _name):
                        old_str_of_interest = in_file_str[fm.get_source_var_declaration(v.name)['start']:(fm.get_source_var_declaration(v.name)['start']+fm.get_source_var_declaration(v.name)['length'])]
                        (new_str_of_interest, num_repl) = re.subn(_name, _name.capitalize(),old_str_of_interest, 1)
                        patches.append({
                            "detector" : "naming-convention (enum use)",
                            "start" : fm.get_source_var_declaration(v.name)['start'],
                            "end" : fm.get_source_var_declaration(v.name)['start'] + fm.get_source_var_declaration(v.name)['length'],
                            "old_string" : old_str_of_interest,
                            "new_string" : new_str_of_interest,
                            "patch_file" : _in_file
                        })
                # To-do Capture Enum uses such as "num = numbers.ONE;"
                # where numbers is not captured by slither as a variable/value on the RHS
            # To-do: Check any other place/way where enum type is used

def create_patch_naming_convention_struct_definition(_slither, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
    global patches
    for contract in _slither.contracts_derived:
        if (contract.name == _contract_name):
            for struct in contract.structures:
                if (struct.name == _name):
                    with open(_in_file, 'r+') as in_file:
                        in_file_str = in_file.read()
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"struct"+r'(.*)'+_name, r'\1'+"struct"+r'\2'+_name[0].capitalize()+_name[1:], old_str_of_interest, 1)
                        if num_repl != 0:
                            patches.append({
                                "detector" : "naming-convention (struct definition)",
                                "start" : _modify_loc_start,
                                "end" : _modify_loc_end,
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest,
                                "patch_file" : _in_file
                            })
                        else:
                            print("Error: Could not find struct?!")
                            sys.exit(-1)
    
def create_patch_naming_convention_struct_uses(_slither, _name, _contract_name, _in_file):
    global patches
    for contract in _slither.contracts_derived:
        with open(_in_file, 'r+') as in_file:
            in_file_str = in_file.read()
            # Check state variables of struct type
            # To-do: Deep-check aggregate types (struct and mapping)
            svs = contract.variables
            for sv in svs:
                if (str(sv.type) == _contract_name + "." + _name):
                    old_str_of_interest = in_file_str[contract.get_source_var_declaration(sv.name)['start']:(contract.get_source_var_declaration(sv.name)['start']+contract.get_source_var_declaration(sv.name)['length'])]
                    (new_str_of_interest, num_repl) = re.subn(_name, _name.capitalize(),old_str_of_interest, 1)
                    patches.append({
                        "detector" : "naming-convention (struct use)",
                        "start" : contract.get_source_var_declaration(sv.name)['start'],
                        "end" : contract.get_source_var_declaration(sv.name)['start'] + contract.get_source_var_declaration(sv.name)['length'],
                        "old_string" : old_str_of_interest,
                        "new_string" : new_str_of_interest,
                        "patch_file" : _in_file
                    })
            # Check function+modifier locals+parameters+returns
            # To-do: Deep-check aggregate types (struct and mapping)
            fms = contract.functions + contract.modifiers
            for fm in fms:
                for v in fm.variables:
                    if (str(v.type) == _contract_name + "." + _name):
                        old_str_of_interest = in_file_str[fm.get_source_var_declaration(v.name)['start']:(fm.get_source_var_declaration(v.name)['start']+fm.get_source_var_declaration(v.name)['length'])]
                        (new_str_of_interest, num_repl) = re.subn(_name, _name.capitalize(),old_str_of_interest, 1)
                        patches.append({
                            "detector" : "naming-convention (struct use)",
                            "start" : fm.get_source_var_declaration(v.name)['start'],
                            "end" : fm.get_source_var_declaration(v.name)['start'] + fm.get_source_var_declaration(v.name)['length'],
                            "old_string" : old_str_of_interest,
                            "new_string" : new_str_of_interest,
                            "patch_file" : _in_file
                        })
            # To-do: Check any other place/way where struct type is used (e.g. typecast)

def create_patch_unused_state(_in_file, _modify_loc_start):
    with open(_in_file, 'r+') as in_file:
        in_file_str = in_file.read()
        old_str_of_interest = in_file_str[_modify_loc_start:]
        patches.append({
            "detector" : "unused-state",
            "start" : _modify_loc_start,
            "end" : _modify_loc_start + len(old_str_of_interest.partition(';')[0]),
            "old_string" : old_str_of_interest.partition(';')[0] + old_str_of_interest.partition(';')[1],
            "new_string" : "",
            "patch_file" : _in_file
        })

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
                "new_string" : new_str_of_interest,
                "patch_file" : _in_file
            })
        else:
            print("Error: No public visibility specifier exists. Regex failed to add extern specifier!")
            sys.exit(-1)

def create_patch_constant_function(_in_file, _match_text, _replace_text, _modify_loc_start, _modify_loc_end):
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
                "new_string" : new_str_of_interest,
                "patch_file" : _in_file
            })
        else:
            print("Error: No view/pure/constant specifier exists. Regex failed to remove specifier!")
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
                "new_string" : new_str_of_interest,
                "patch_file" : _in_file
            })
        else:
            print("Error: State variable not found?!")
            sys.exit(-1)

def create_patch_different_pragma(_in_file, pragma, _modify_loc_start, _modify_loc_end):
    with open(_in_file, 'r+') as in_file:
        in_file_str = in_file.read()
        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
        patches.append({
            "detector" : "pragma",
	    "start" : _modify_loc_start,
	    "end" : _modify_loc_end,
	    "old_string" : old_str_of_interest,
	    "new_string" : pragma,
            "patch_file" : _in_file
        })

def create_patch_solc_version(_in_file, _solc_version, _modify_loc_start, _modify_loc_end):
 with open(_in_file, 'r+') as in_file:
        in_file_str = in_file.read()
        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
        patches.append({
            "detector" : "solc-version",
	    "start" : _modify_loc_start,
	    "end" : _modify_loc_end,
	    "old_string" : old_str_of_interest,
	    "new_string" : _solc_version,
            "patch_file" : _in_file
        })
    
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
