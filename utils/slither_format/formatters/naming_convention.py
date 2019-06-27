import re
import logging
from collections import namedtuple
from slither.exceptions import SlitherException
from slither.core.expressions.identifier import Identifier
from slither.slithir.operations import NewContract
from slither.slithir.operations import Member
from ..utils.patches import create_patch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Slither.Format')

def format(slither, result):
    elements = result['elements']
    for element in elements:
        target = element['additional_fields']['target']

        convention = element['additional_fields']['convention']

        if convention == "l_O_I_should_not_be_used":
            # l_O_I_should_not_be_used cannot be automatically patched
            logger.info(f'The following naming convention cannot be patched: \n{result["description"]}')
            continue

        _patch(slither, result, element, target)

# endregion
###################################################################################
###################################################################################
# region Helpers
###################################################################################
###################################################################################

def _unpack_info(slither, element):
    path = element['source_mapping']['filename_absolute']
    source_code = slither.source_code[path].encode('utf-8')

    loc_start = element['source_mapping']['start']
    loc_end = loc_start + element['source_mapping']['length']
    old_string = source_code[loc_start:loc_end]
    return path, source_code, old_string, loc_start, loc_end

def get_name(element):
    return element['name']

def get_contract_name(element):
    target = element['additional_fields']['target']
    if target == "parameter":
        return element['type_specific_fields']['parent']['type_specific_fields']['parent']['name']
    elif target in ["modifier", "function", "event",
                    "variable", "variable_constant", "enum",
                    "structure"]:
        return element['type_specific_fields']['parent']['name']
    return element['name']


# endregion
###################################################################################
###################################################################################
# region Patch dispatcher
###################################################################################
###################################################################################

def _patch(slither, result, element, _target):

    if _target == "contract":
        _create_patch_contract_definition(slither, result, element)
        _create_patch_contract_uses(slither, result, element)

    elif _target == "structure":
        _create_patch_struct_definition(slither, result, element)
        _create_patch_struct_uses(slither, result, element)

    elif _target == "event":
        _create_patch_event_definition(slither, result, element)
        _create_patch_event_calls(slither, result, element)

    elif _target == "function":
        # Avoid constructor (FP?)
        if element['name'] != element['type_specific_fields']['parent']['name']:
            _create_patch_function_definition(slither, result, element)
            _create_patch_function_calls(slither, result, element)

    elif _target == "parameter":
        _create_patch_parameter_declaration(slither, result, element)
        _create_patch_parameter_uses(slither, result, element)

    elif _target == "variable":
        _create_patch_state_variable_declaration(slither, result, element)
        _create_patch_state_variable_uses(slither, result, element)

    elif _target == "variable_constant":
        _create_patch_state_variable_constant_declaration(slither, result, element)
        _create_patch_state_variable_uses(slither, result, element)

    elif _target == "enum":
        _create_patch_enum_declaration(slither, result, element)
        _create_patch_enum_uses(slither, result, element)

    elif _target == "modifier":
        _create_patch_modifier_definition(slither, result, element)
        _create_patch_modifier_uses(slither, result, element)

    else:
        raise SlitherException("Unknown naming convention! " + _target)

# endregion
###################################################################################
###################################################################################
# region Declaration and Definition
###################################################################################
###################################################################################


def _create_patch_contract_definition(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)

    name = get_name(element)

    # Locate the name following keywords `contract` | `interface` | `library`
    m = re.match(r'(.*)' + "(contract|interface|library)" + r'(.*)' + name, old_str_of_interest.decode('utf-8'))

    old_str_of_interest = in_file_str[loc_start:loc_start+m.span()[1]]
    # Capitalize the name
    (new_string, num_repl) = re.subn(r'(.*)' + r'(contract|interface|library)' + r'(.*)' + name,
                                              r'\1' + r'\2' + r'\3' + name.capitalize(),
                                              old_str_of_interest.decode('utf-8'), 1)

    if num_repl == 0:
        raise SlitherException(f"Could not find contract: {name}")

    old_string = old_str_of_interest.decode('utf-8')

    loc_end = loc_start + m.span()[1]

    create_patch(result,
                 in_file,
                 loc_start,
                 loc_end,
                 old_string,
                 new_string)


def _create_patch_state_variable_declaration(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)

    name = get_name(element)

    m = re.search(name, old_str_of_interest.decode('utf-8'))
    # Skip rare cases where re search fails. To-do: Investigate
    if not m:
        return None
    new_string = old_str_of_interest.decode('utf-8')[m.span()[0]:m.span()[1]]
    new_string = new_string[0].lower() + new_string[1:]

    old_string = old_str_of_interest.decode('utf-8')[m.span()[0]:m.span()[1]]

    loc_end = loc_start + m.span()[1]
    loc_start = loc_start + m.span()[0]

    create_patch(result,
                 in_file,
                 loc_start,
                 loc_end,
                 old_string,
                 new_string)


def _create_patch_state_variable_constant_declaration(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, _ = _unpack_info(slither, element)

    name = get_name(element)

    m = re.search(name, old_str_of_interest.decode('utf-8'))
    # Skip rare cases where re search fails. To-do: Investigate
    if not m:
        return None
    # Convert constant state variables to upper case
    new_string = old_str_of_interest.decode('utf-8')[m.span()[0]:m.span()[1]].upper()

    old_string = old_str_of_interest.decode('utf-8')[m.span()[0]:m.span()[1]]
    loc_end = loc_start + m.span()[1]
    loc_start = loc_start + m.span()[0]

    create_patch(result,
                 in_file,
                 loc_start,
                 loc_end,
                 old_string,
                 new_string)


def _create_patch_enum_declaration(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)

    name = get_name(element)

    m = re.search(name, old_str_of_interest.decode('utf-8'))
    # Skip rare cases where re search fails. To-do: Investigate
    if not m:
        return None
    # Search for the enum name after the `enum` keyword
    # Capitalize enum name
    (new_string, num_repl) = re.subn(r'(.*)' + "enum" + r'(.*)' + name, r'\1' + "enum" + r'\2' +
                                              name[0].capitalize() + name[1:],
                                              old_str_of_interest.decode('utf-8'), 1)

    if num_repl == 0:
        raise SlitherException(f"Could not find enum: {name}")

    old_string = old_str_of_interest.decode('utf-8')

    create_patch(result,
                 in_file,
                 loc_start,
                 loc_end,
                 old_string,
                 new_string)


def _create_patch_struct_definition(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)

    name = get_name(element)

    m = re.search(name, old_str_of_interest.decode('utf-8'))
    # Skip rare cases where re search fails. To-do: Investigate
    if not m:
        return None
    # Capitalize the struct name beyond the keyword `struct`

    (new_string, num_repl) = re.subn(r'(.*)'+"struct"+r'(.*)'+name, r'\1'+"struct"+r'\2'+
                                     name.capitalize(),
                                     old_str_of_interest.decode('utf-8'), 1)

    if num_repl == 0:
        raise SlitherException(f"Could not find struct: {name}")

    old_string = old_str_of_interest.decode('utf-8')

    create_patch(result,
                 in_file,
                 loc_start,
                 loc_end,
                 old_string,
                 new_string)


def _create_patch_modifier_definition(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)
    name = get_name(element)

    in_file_str = slither.source_code[in_file].encode('utf-8')
    old_str_of_interest = in_file_str[loc_start:loc_end]
    # Search for the modifier name after the `modifier` keyword
    m = re.match(r'(.*)'+"modifier"+r'(.*)'+name, old_str_of_interest.decode('utf-8'))
    old_str_of_interest = in_file_str[loc_start:loc_end+m.span()[1]]
    # Change the first letter of the modifier name to lowercase
    (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"modifier"+r'(.*)'+name, r'\1'+"modifier"+r'\2' +
                                              name[0].lower()+name[1:], old_str_of_interest.decode('utf-8'), 1)
    if num_repl != 0:
        create_patch(result,
                     in_file,
                     loc_start,
                     loc_end + m.span()[1],
                     old_str_of_interest.decode('utf-8'),
                     new_str_of_interest)
    else:
        raise SlitherException("Could not find modifier?!")


def _create_patch_function_definition(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)
    name = get_name(element)

    in_file_str = slither.source_code[in_file].encode('utf-8')
    old_str_of_interest = in_file_str[loc_start:loc_end]
    # Search for the function name after the `function` keyword
    m = re.match(r'(.*)'+"function"+r'\s*'+name, old_str_of_interest.decode('utf-8'))
    old_str_of_interest = in_file_str[loc_start:loc_start+m.span()[1]]
    # Change the first letter of the function name to lowercase
    (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"function"+r'(.*)'+name, r'\1'+"function"+r'\2'+
                                              name[0].lower()+name[1:], old_str_of_interest.decode('utf-8'), 1)
    if num_repl != 0:
        create_patch(result,
                     in_file,
                     loc_start,
                     loc_start+m.span()[1],
                     old_str_of_interest.decode('utf-8'),
                     new_str_of_interest)

    else:
        raise SlitherException(f"Could not find function {name}")

def _create_patch_event_definition(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)

    name = get_name(element)
    contract_name = get_contract_name(element)

    target_contract = slither.get_contract_from_name(contract_name)
    if not target_contract:
        raise SlitherException("Contract not found?!")
    for event in target_contract.events:
        if event.name == name:
            # Get only event name without parameters
            event_name = name.split('(')[0]
            f_event = event.source_mapping['filename_absolute']
            in_file_str = slither.source_code[f_event].encode('utf-8')
            old_str_of_interest = in_file_str[loc_start:loc_end]
            # Capitalize event name
            (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"event"+r'(.*)'+event_name, r'\1'+"event"+r'\2' +
                                                      event_name.capitalize(),
                                                      old_str_of_interest.decode('utf-8'), 1)
            if num_repl != 0:
                create_patch(result,
                             f_event,
                             loc_start,
                             loc_end,
                             old_str_of_interest.decode('utf-8'),
                             new_str_of_interest)
            else:
                raise SlitherException("Could not find event?!")

def _create_patch_parameter_declaration(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)
    name = get_name(element)

    # To-do: Change format logic below - how do we convert a name to mixedCase?
    if(name[0] == '_'):
        # If parameter name begins with underscore, capitalize the letter after underscore
        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+name[0]+name[1].upper() +
                                                  name[2:]+r'\2', old_str_of_interest.decode('utf-8'), 1)
    else:
        # Add underscore and capitalize the first letter
        (new_str_of_interest, num_repl) = re.subn(r'(.*)' + name + r'(.*)', r'\1' + '_' + name.capitalize() +
                                                  r'\2', old_str_of_interest.decode('utf-8'), 1)
    if num_repl != 0:
        create_patch(result,
                     in_file,
                     loc_start,
                     loc_end,
                     old_str_of_interest.decode('utf-8'),
                     new_str_of_interest)
    else:
        raise SlitherException("Could not find parameter declaration?!")

# endregion
###################################################################################
###################################################################################
# region Usage patches
###################################################################################
###################################################################################

def _create_patch_contract_uses(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)

    name = get_name(element)

    target_contract = slither.get_contract_from_name(name)
    if not target_contract:
        raise SlitherException(f"Contract not found {name}")

    # Check state variables of contract type
    # To-do: Deep-check aggregate types (struct and mapping)
    svs = target_contract.variables
    for sv in svs:
        if (str(sv.type) == name):
            old_str_of_interest = in_file_str[sv.source_mapping['start']:(sv.source_mapping['start'] +
                                                                          sv.source_mapping['length'])]
            # Get only the contract variable name even if it is initialised
            (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),
                                                      old_str_of_interest.decode('utf-8'), 1)
            create_patch(result,
                         in_file,
                         sv.source_mapping['start'],
                         sv.source_mapping['start'] + sv.source_mapping['length'],
                         old_str_of_interest.decode('utf-8'),
                         new_str_of_interest)
    # Check function+modifier locals+parameters+returns
    # To-do: Deep-check aggregate types (struct and mapping)
    fms = target_contract.functions + target_contract.modifiers
    for fm in fms:
        for v in fm.variables:
            if (str(v.type) == name):
                old_str_of_interest = in_file_str[v.source_mapping['start']:(v.source_mapping['start'] +
                                                                             v.source_mapping['length'])]
                old_str_of_interest = old_str_of_interest.decode('utf-8').split('=')[0]
                (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),old_str_of_interest, 1)

                create_patch(result,
                             in_file,
                             v.source_mapping['start'],
                             v.source_mapping['start'] + len(old_str_of_interest),
                             old_str_of_interest,
                             new_str_of_interest)

    # Check "new" expressions for creation of contract objects
    for function in target_contract.functions:
        for node in function.nodes:
            for ir in node.irs:
                if isinstance(ir, NewContract) and ir.contract_name == name:
                    old_str_of_interest = in_file_str[node.source_mapping['start']:node.source_mapping['start'] +
                                                      node.source_mapping['length']]
                    # Search for the name after the `new` keyword
                    m = re.search("new"+r'(.*)'+name, old_str_of_interest.decode('utf-8'))
                    # Skip rare cases where re search fails. To-do: Investigate
                    if not m:
                        continue
                    old_str_of_interest = old_str_of_interest.decode('utf-8')[m.span()[0]:]
                    (new_str_of_interest, num_repl) = re.subn("new" + r'(.*)' + name,
                                                              "new" + r'\1' + name.capitalize(),
                                                              name[1:], old_str_of_interest, 1)
                    if num_repl != 0:
                        create_patch(result,
                                     in_file,
                                     # start after the `new` keyword where the name begins
                                     node.source_mapping['start'] + m.span()[0],
                                     node.source_mapping['start'] + m.span()[1],
                                     old_str_of_interest,
                                     new_str_of_interest)
                    else:
                        raise SlitherException("Could not find new object?!")


def _create_patch_modifier_uses(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)

    name = get_name(element)
    contract_name = get_contract_name(element)

    modifier_sig = element['type_specific_fields']['signature']

    target_contract = slither.get_contract_from_name(contract_name)
    if not target_contract:
        raise SlitherException("Contract not found?!")

    modifier_contract = target_contract.get_modifier_from_signature(modifier_sig)

    for function in target_contract.functions:
        for m in function.modifiers:
            if (m == modifier_contract):
                f_modifier = m.source_mapping['filename_absolute']
                in_file_str = slither.source_code[f_modifier].encode('utf-8')
                # Get the text from function parameters until the return statement or function body beginning
                # This text will include parameter declarations, any Solidity keywords and modifier call
                # Parameter names cannot collide with modifier name per Solidity rules
                old_str_of_interest = in_file_str[int(function.parameters_src.source_mapping['start']):
                                                  int(function.returns_src.source_mapping['start'])]
                # Change the first letter of the modifier name (if present) to lowercase
                (new_str_of_interest, num_repl) = re.subn(name, name[0].lower()+name[1:],
                                                          old_str_of_interest.decode('utf-8'),1)
                if num_repl != 0:
                    create_patch(result,
                                 f_modifier,
                                 int(function.parameters_src.source_mapping['start']),
                                 int(function.returns_src.source_mapping['start']),
                                 old_str_of_interest.decode('utf-8'),
                                 new_str_of_interest)
                else:
                    raise SlitherException("Could not find modifier name?!")



def _create_patch_function_calls(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)
    name = get_name(element)
    contract_name = get_contract_name(element)

    for contract in slither.contracts:
        for function in contract.functions:
            for node in function.nodes:
                # Function call from another contract
                for high_level_call in node.high_level_calls:
                    if (high_level_call[0].name == contract_name and high_level_call[1].name == name):
                        for external_call in node.external_calls_as_expressions:
                            # Check the called function name
                            called_function = str(external_call.called).split('.')[-1]
                            if called_function == high_level_call[1].name:
                                f_external_call = external_call.source_mapping['filename_absolute']
                                in_file_str = slither.source_code[f_external_call].encode('utf-8')
                                old_str_of_interest = in_file_str[int(external_call.source_mapping['start']):
                                                                  int(external_call.source_mapping['start']) +
                                                                  int(external_call.source_mapping['length'])]
                                # Get the called function name. To-do: Check if we need to avoid parameters
                                called_function_name = old_str_of_interest.decode('utf-8').split('.')[-1]
                                # Convert first letter of name to lowercase
                                fixed_function_name = called_function_name[0].lower() + called_function_name[1:]
                                # Reconstruct the entire call
                                new_string = '.'.join(old_str_of_interest.decode('utf-8').split('.')[:-1]) + '.' + \
                                    fixed_function_name
                                create_patch(result,
                                             f_external_call,
                                             external_call.source_mapping['start'],
                                             int(external_call.source_mapping['start']) +
                                             int(external_call.source_mapping['length']),
                                             old_str_of_interest.decode('utf-8'),
                                             new_string)
                # Function call from within same contract
                for internal_call in node.internal_calls_as_expressions:
                    if (str(internal_call.called) == name):
                        f_internal_call = internal_call.source_mapping['filename_absolute']
                        in_file_str = slither.source_code[f_internal_call].encode('utf-8')
                        old_str_of_interest = in_file_str[int(internal_call.source_mapping['start']):
                                                          int(internal_call.source_mapping['start']) +
                                                          int(internal_call.source_mapping['length'])]
                        # Get the called function name and avoid parameters
                        old_str_of_interest = old_str_of_interest.decode('utf-8').split('(')[0]
                        # Avoid parameters
                        # TODO: (JF) review me
                        end_loc = int(internal_call.source_mapping['start']) + \
                            int(internal_call.source_mapping['length']) - \
                            len('('.join(in_file_str[int(internal_call.source_mapping['start']):
                                                     int(internal_call.source_mapping['start']) +
                                                     int(internal_call.source_mapping['length'])] \
                                         .decode('utf-8').split('(')[1:])) - 1
                        create_patch(result,
                                     f_internal_call,
                                     internal_call.source_mapping['start'],
                                     end_loc,
                                     old_str_of_interest,
                                     old_str_of_interest[0].lower()+old_str_of_interest[1:])




def _create_patch_event_calls(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)

    name = get_name(element)
    contract_name = get_contract_name(element)

    # Get only event name without parameters
    event_name = name.split('(')[0]
    target_contract = slither.get_contract_from_name(contract_name)
    if not target_contract:
        raise SlitherException("Contract not found?!")
    for contract in [target_contract] + target_contract.derived_contracts:
        for function in contract.functions:
            for node in function.nodes:
                for call in node.internal_calls_as_expressions:
                    if (str(call.called) == event_name):
                        f_call = call.source_mapping['filename_absolute']
                        in_file_str = slither.source_code[f_call].encode('utf-8')
                        old_str_of_interest = in_file_str[int(call.source_mapping['start']):
                                                          int(call.source_mapping['start']) +
                                                          int(call.source_mapping['length'])]

                        create_patch(result,
                                     f_call,
                                     call.source_mapping['start'],
                                     int(call.source_mapping['start']) + int(call.source_mapping['length']),
                                     old_str_of_interest.decode('utf-8'),
                                     # Capitalize event name
                                     old_str_of_interest.decode('utf-8').capitalize())


def _create_patch_parameter_uses(slither, result, element):

    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)

    name = get_name(element)
    contract_name = get_contract_name(element)

    function_sig = element['type_specific_fields']['parent']['type_specific_fields']['signature']

    target_contract = slither.get_contract_from_name(contract_name)
    function = target_contract.get_function_from_signature(function_sig)

    for node in function.nodes:
        # _expression_* are used to access the source mapping of the call rather
        # than the body definition
        vars = node._expression_vars_written + node._expression_vars_read
        for v in vars:
            if isinstance(v, Identifier) and str(v) == name and [str(lv) for lv in
                                                                 (node._local_vars_read +
                                                                  node._local_vars_written)
                                                                 if str(lv) == name]:
                # Skip rare cases where source_mapping is absent. To-do: Investigate
                if not v.source_mapping:
                    continue
                modify_loc_start = int(v.source_mapping['start'])
                modify_loc_end = int(v.source_mapping['start']) + int(v.source_mapping['length'])
                old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                # To-do: Change format logic below - how do we convert a name to mixedCase?
                if(name[0] == '_'):
                    # If parameter name begins with underscore, capitalize the letter after underscore
                    (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)',
                                                              r'\1'+name[0]+name[1].upper()+name[2:] +
                                                              r'\2', old_str_of_interest.decode('utf-8'),
                                                              1)
                else:
                    # Add underscore and capitalize the first letter
                    (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+'_' +
                                                              name.capitalize()+r'\2',
                                                              old_str_of_interest.decode('utf-8'), 1)
                if num_repl != 0:
                    create_patch(result,
                                 in_file,
                                 modify_loc_start,
                                 modify_loc_end,
                                 old_str_of_interest.decode('utf-8'),
                                 new_str_of_interest)
                else:
                    raise SlitherException("Could not find parameter use?!")

    # Process function parameters passed to modifiers
    # _expression_modifiers is used to access the source mapping of the call rather
    # than the body definition
    for modifier in function._expression_modifiers:
        for arg in modifier.arguments:
            if str(arg) == name:
                old_str_of_interest = in_file_str[modifier.source_mapping['start']:
                                                  modifier.source_mapping['start'] +
                                                  modifier.source_mapping['length']]
                # Get text beyond modifier name which contains parameters
                old_str_of_interest_beyond_modifier_name = old_str_of_interest.decode('utf-8')\
                                                                              .split('(')[1]
                # To-do: Change format logic below - how do we convert a name to mixedCase?
                if(name[0] == '_'):
                    # If parameter name begins with underscore, capitalize the letter after underscore
                    (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+name[0]+
                                                              name[1].upper()+name[2:]+r'\2',
                                                              old_str_of_interest_beyond_modifier_name, 1)
                else:
                    # Add underscore and capitalize the first letter
                    (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+'_'+
                                                              name.capitalize()+r'\2',
                                                              old_str_of_interest_beyond_modifier_name, 1)
                if num_repl != 0:
                    create_patch(result,
                                 in_file,
                                 # Start beyond modifier name which contains parameters
                                 modifier.source_mapping['start'] +
                                 len(old_str_of_interest.decode('utf-8').split('(')[0]) + 1,
                                 modifier.source_mapping['start'] + modifier.source_mapping['length'],
                                 old_str_of_interest_beyond_modifier_name,
                                 new_str_of_interest)
                else:
                    raise SlitherException("Could not find parameter use in modifier?!")



def _create_patch_state_variable_uses(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)

    name = get_name(element)
    contract_name = get_contract_name(element)

    # To-do: Check cross-contract state variable uses
    target_contract = slither.get_contract_from_name(contract_name)
    if not target_contract:
        raise SlitherException(f"Contract not found {contract_name}")

    fms = target_contract.functions + target_contract.modifiers
    for fm in fms:
        for node in fm.nodes:
            vars = node._expression_vars_written + node._expression_vars_read
            for v in vars:
                if isinstance(v, Identifier) and str(v) == name and [str(sv) for sv in
                                                                     (node._state_vars_read +
                                                                      node._state_vars_written)
                                                                     if str(sv) == name]:
                    modify_loc_start = int(v.source_mapping['start'])
                    modify_loc_end = int(v.source_mapping['start']) + int(v.source_mapping['length'])
                    f_function = fm.source_mapping['filename_absolute']
                    in_file_str = slither.source_code[f_function].encode('utf-8')
                    old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                    if (element['additional_fields']['target'] == "variable_constant"):
                        # Convert constant state variables to upper case
                        new_str_of_interest = old_str_of_interest.decode('utf-8').upper()
                    else:
                        new_str_of_interest = old_str_of_interest.decode('utf-8')
                        new_str_of_interest = new_str_of_interest[0].lower()+new_str_of_interest[1:]

                    create_patch(result,
                                 f_function,
                                 modify_loc_start,
                                 modify_loc_end,
                                 old_str_of_interest.decode('utf-8'),
                                 new_str_of_interest)



def _create_patch_enum_uses(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)

    name = get_name(element)
    contract_name = get_contract_name(element)

    target_contract = slither.get_contract_from_name(contract_name)
    if not target_contract:
        raise SlitherException(f"Contract not found {contract_name}")

    in_file_str = slither.source_code[in_file].encode('utf-8')
    # Check state variable declarations of enum type
    # To-do: Deep-check aggregate types (struct and mapping)
    svs = target_contract.variables
    for sv in svs:
        if (str(sv.type) == contract_name + "." + name):
            old_str_of_interest = in_file_str[sv.source_mapping['start']:(sv.source_mapping['start']+
                                                                          sv.source_mapping['length'])]
            (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),
                                                      old_str_of_interest.decode('utf-8'), 1)

            create_patch(result,
                         in_file,
                         sv.source_mapping['start'],
                         sv.source_mapping['start'] + sv.source_mapping['length'],
                         old_str_of_interest.decode('utf-8'),
                         new_str_of_interest)

    # Check function+modifier locals+parameters+returns
    # To-do: Deep-check aggregate types (struct and mapping)
    fms = target_contract.functions + target_contract.modifiers
    for fm in fms:
        # Enum declarations
        for v in fm.variables:
            if (str(v.type) == contract_name + "." + name):
                old_str_of_interest = in_file_str[v.source_mapping['start']:(v.source_mapping['start']+
                                                                             v.source_mapping['length'])]
                (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),
                                                          old_str_of_interest.decode('utf-8'), 1)

                create_patch(result,
                             in_file,
                             v.source_mapping['start'],
                             v.source_mapping['start'] + v.source_mapping['length'],
                             old_str_of_interest.decode('utf-8'),
                             new_str_of_interest)

    # Capture enum uses such as "num = numbers.ONE;"
    for function in target_contract.functions:
        for node in function.nodes:
            for ir in node.irs:
                if isinstance(ir, Member):
                    if str(ir.variable_left) == name:
                        # Skip past the assignment
                        old_str_of_interest = in_file_str[node.source_mapping['start']:
                                                          (node.source_mapping['start']+
                                                           node.source_mapping['length'])].decode('utf-8')\
                                                           .split('=')[1]
                        m = re.search(r'(.*)'+name, old_str_of_interest)
                        # Skip rare cases where re search fails. To-do: Investigate
                        if not m:
                            continue
                        old_str_of_interest = old_str_of_interest[m.span()[0]:]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name, r'\1'+name.capitalize(),
                                                                  old_str_of_interest, 1)
                        if num_repl != 0:

                            # TODO (JF): review me
                            # Start past the assignment
                            loc_start = node.source_mapping['start'] + \
                                len(in_file_str[node.source_mapping['start']:
                                                (node.source_mapping['start']+
                                                 node.source_mapping['length'])].decode('utf-8').split('=')[0]) + \
                                1 + m.span()[0]

                            # End accounts for the assignment from the start
                            loc_end = node.source_mapping['start'] +\
                                len(in_file_str[node.source_mapping['start']:(node.source_mapping['start']+
                                                                              node.source_mapping['length'])].\
                                    decode('utf-8').split('=')[0]) + 1 + m.span()[0] + len(old_str_of_interest)

                            create_patch(result,
                                         in_file,
                                         loc_start,
                                         loc_end,
                                         old_str_of_interest,
                                         new_str_of_interest)

                        else:
                            raise SlitherException("Could not find new object?!")
        # To-do: Check any other place/way where enum type is used





def _create_patch_struct_uses(slither, result, element):
    in_file, in_file_str, old_str_of_interest, loc_start, loc_end = _unpack_info(slither, element)

    name = get_name(element)
    contract_name = get_contract_name(element)

    target_contract = slither.get_contract_from_name(contract_name)
    if not target_contract:
        raise SlitherException(f"Contract not found {contract_name}")

    for contract in [target_contract] + target_contract.derived_contracts:
        f_contract = contract.source_mapping['filename_absolute']
        in_file_str = slither.source_code[f_contract].encode('utf-8')
        # Check state variables of struct type
        # To-do: Deep-check aggregate types (struct and mapping)
        svs = contract.variables
        for sv in svs:
            if (str(sv.type) == contract_name + "." + name):
                old_str_of_interest = in_file_str[sv.source_mapping['start']:(sv.source_mapping['start']+
                                                                              sv.source_mapping['length'])]
                (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),
                                                          old_str_of_interest.decode('utf-8'), 1)

                create_patch(result,
                             f_contract,
                             sv.source_mapping['start'],
                             sv.source_mapping['start'] + sv.source_mapping['length'],
                             old_str_of_interest.decode('utf-8'),
                             new_str_of_interest)
        # Check function+modifier locals+parameters+returns
        # To-do: Deep-check aggregate types (struct and mapping)
        fms = contract.functions + contract.modifiers
        for fm in fms:
            for v in fm.variables:
                if (str(v.type) == contract_name + "." + name):
                    old_str_of_interest = in_file_str[v.source_mapping['start']:(v.source_mapping['start']+
                                                                                 v.source_mapping['length'])]
                    (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),
                                                              old_str_of_interest.decode('utf-8'), 1)

                    create_patch(result,
                                 in_file,
                                 v.source_mapping['start'],
                                 v.source_mapping['start'] + v.source_mapping['length'],
                                 old_str_of_interest.decode('utf-8'),
                                 new_str_of_interest)
        # To-do: Check any other place/way where struct type is used (e.g. typecast)



# endregion
