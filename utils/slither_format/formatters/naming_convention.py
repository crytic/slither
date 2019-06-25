import re
from collections import namedtuple
from slither.exceptions import SlitherException
from slither.core.expressions.identifier import Identifier
from slither.slithir.operations import NewContract
from slither.slithir.operations import Member

# The Namedtuple will be used to give all the parameters from _patch to the _create_X functions
# Its used to improve code readability and avoid incorrect parameters order
FormatInfo = namedtuple("FormatInfo", ["slither",
                                       "patches",
                                       "target",
                                       "name",
                                       "function_name",
                                       "contract_name",
                                       "in_file",
                                       "in_file_relative",
                                       "loc_start",
                                       "loc_end"])


def format(slither, patches, elements):
    for element in elements:
        target = element['additional_fields']['target']
        if (target == "parameter"):
            _patch(slither, patches,
                   element['additional_fields']['target'],
                   element['name'],
                   element['type_specific_fields']['parent']['name'],
                   element['type_specific_fields']['parent']['type_specific_fields']['parent']['name'],
                   element['source_mapping']['filename_absolute'],
                   element['source_mapping']['filename_relative'],
                   element['source_mapping']['start'],
                   (element['source_mapping']['start'] + element['source_mapping']['length']))

        elif target in ["modifier", "function", "event",
                        "variable", "variable_constant", "enum"
                        "structure"]:
            _patch(slither, patches, target,
                   element['name'], element['name'],
                   element['type_specific_fields']['parent']['name'],
                   element['source_mapping']['filename_absolute'],
                   element['source_mapping']['filename_relative'],
                   element['source_mapping']['start'],
                   (element['source_mapping']['start'] + element['source_mapping']['length']))
        else:
            _patch(slither, patches, element['additional_fields']['target'],
                   element['name'], element['name'], element['name'],
                   element['source_mapping']['filename_absolute'],
                   element['source_mapping']['filename_relative'],
                   element['source_mapping']['start'],
                   (element['source_mapping']['start'] + element['source_mapping']['length']))


def _patch(slither, patches, _target, name, function_name, contract_name, in_file, in_file_relative,
                 modify_loc_start, modify_loc_end):

    format_info = FormatInfo(slither,
                             patches,
                             _target,
                             name,
                             function_name,
                             contract_name,
                             in_file,
                             in_file_relative,
                             modify_loc_start,
                             modify_loc_end)

    if _target == "contract":
        _create_patch_contract_definition(format_info)

        _create_patch_contract_uses(format_info)
    elif _target == "structure":
        _create_patch_struct_definition(format_info)

        _create_patch_struct_uses(format_info)
    elif _target == "event":
        _create_patch_event_definition(format_info)

        _create_patch_event_calls(format_info)

    elif _target == "function":
        if name != contract_name:
            _create_patch_function_definition(format_info)

            _create_patch_function_calls(format_info)
    elif _target == "parameter":
        _create_patch_parameter_declaration(format_info)

        _create_patch_parameter_uses(format_info)

    elif _target in ["variable_constant", "variable"]:
        _create_patch_state_variable_declaration(format_info)

        _create_patch_state_variable_uses(format_info)
    elif _target == "enum":
        _create_patch_enum_definition(format_info)
        _create_patch_enum_uses(format_info)
    elif _target == "modifier":
        _create_patch_modifier_definition(format_info)
        _create_patch_modifier_uses(format_info)
    else:
        raise SlitherException("Unknown naming convention! " + _target)


        

def _create_patch_contract_definition(format_info):
    in_file_str = format_info.slither.source_code[format_info.in_file].encode('utf-8')
    old_str_of_interest = in_file_str[format_info.loc_start:format_info.loc_end]
    m = re.match(r'(.*)'+"contract"+r'(.*)'+format_info.name, old_str_of_interest.decode('utf-8'))
    old_str_of_interest = in_file_str[format_info.loc_start:format_info.loc_start+m.span()[1]]
    (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"contract"+r'(.*)'+format_info.name,
                                              r'\1'+"contract"+r'\2'+format_info.name.capitalize(),
                                              old_str_of_interest.decode('utf-8'), 1)
    if num_repl != 0:
        patch = {
            "file" : format_info.in_file,
            "detector" : "naming-convention (contract definition)",
            "start": format_info.loc_start,
            "end": format_info.loc_start+m.span()[1],
            "old_string":old_str_of_interest.decode('utf-8'),
            "new_string":new_str_of_interest
        }
        if not patch in format_info.patches[format_info.in_file_relative]:
            format_info.patches[format_info.in_file_relative].append(patch)
    else:
        raise SlitherException("Could not find contract?!")


def _create_patch_contract_uses(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative

    for contract in slither.contracts:
        # Ignore contract definition
        if contract.name != name:
            in_file_str = slither.source_code[in_file].encode('utf-8')
            # Check state variables of contract type
            # To-do: Deep-check aggregate types (struct and mapping)
            svs = contract.variables
            for sv in svs:
                if (str(sv.type) == name):
                    old_str_of_interest = in_file_str[sv.source_mapping['start']:(sv.source_mapping['start'] +
                                                                                  sv.source_mapping['length'])]
                    (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),
                                                              old_str_of_interest.decode('utf-8'), 1)
                    patch = {
                        "file" : in_file,
                        "detector" : "naming-convention (contract state variable)",
                        "start" : sv.source_mapping['start'],
                        "end" : sv.source_mapping['start'] + sv.source_mapping['length'],
                        "old_string" : old_str_of_interest.decode('utf-8'),
                        "new_string" : new_str_of_interest
                    }
                    if not patch in patches[in_file_relative]:
                        patches[in_file_relative].append(patch)
            # Check function+modifier locals+parameters+returns
            # To-do: Deep-check aggregate types (struct and mapping)
            fms = contract.functions + contract.modifiers
            for fm in fms:
                for v in fm.variables:
                    if (str(v.type) == name):
                        old_str_of_interest = in_file_str[v.source_mapping['start']:(v.source_mapping['start'] +
                                                                                     v.source_mapping['length'])]
                        old_str_of_interest = old_str_of_interest.decode('utf-8').split('=')[0]
                        (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),old_str_of_interest, 1)
                        patch = {
                            "file" : in_file,
                            "detector" : "naming-convention (contract function variable)",
                            "start" : v.source_mapping['start'],
                            "end" : v.source_mapping['start'] + len(old_str_of_interest),
                            "old_string" : old_str_of_interest,
                            "new_string" : new_str_of_interest
                        }
                        if not patch in patches[in_file_relative]:
                            patches[in_file_relative].append(patch)
            # Check "new" expressions for creation of contract objects
            for function in contract.functions:
                for node in function.nodes:
                    for ir in node.irs:
                        if isinstance(ir, NewContract) and ir.contract_name == name:
                            old_str_of_interest = in_file_str[node.source_mapping['start']:node.source_mapping['start'] +
                                                              node.source_mapping['length']]
                            m = re.search("new"+r'(.*)'+name, old_str_of_interest.decode('utf-8'))
                            old_str_of_interest = old_str_of_interest.decode('utf-8')[m.span()[0]:]
                            (new_str_of_interest, num_repl) = re.subn("new"+r'(.*)'+name, "new"+r'\1'+name[0].upper() +
                                                                      name[1:], old_str_of_interest, 1)
                            if num_repl != 0:
                                patch = {
                                    "file" : in_file,
                                    "detector" : "naming-convention (contract new object)",
                                    "start" : node.source_mapping['start'] + m.span()[0],
                                    "end" : node.source_mapping['start'] + m.span()[1],
                                    "old_string" : old_str_of_interest,
                                    "new_string" : new_str_of_interest
                                }
                                if not patch in patches[in_file_relative]:
                                    patches[in_file_relative].append(patch)
                            else:
                                raise SlitherException("Could not find new object?!")


def _create_patch_modifier_definition(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative
    contract_name = format_info.contract_name
    modify_loc_start, modify_loc_end = format_info.loc_start, format_info.loc_end

    target_contract = slither.get_contract_from_name(contract_name)
    if not target_contract:
        raise SlitherException("Contract not found?!")
    for modifier in target_contract.modifiers:
        if modifier.name == name:
            in_file_str = slither.source_code[in_file].encode('utf-8')
            old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
            m = re.match(r'(.*)'+"modifier"+r'(.*)'+name, old_str_of_interest.decode('utf-8'))
            old_str_of_interest = in_file_str[modify_loc_start:modify_loc_start+m.span()[1]]
            (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"modifier"+r'(.*)'+name, r'\1'+"modifier"+r'\2' +
                                                      name[0].lower()+name[1:], old_str_of_interest.decode('utf-8'), 1)
            if num_repl != 0:
                patch = {
                    "file" : in_file,
                    "detector" : "naming-convention (modifier definition)",
                    "start" : modify_loc_start,
                    "end" : modify_loc_start+m.span()[1],
                    "old_string" : old_str_of_interest.decode('utf-8'),
                    "new_string" : new_str_of_interest
                }
                if not patch in patches[in_file_relative]:
                    patches[in_file_relative].append(patch)
            else:
                raise SlitherException("Could not find modifier?!")


def _create_patch_modifier_uses(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative
    contract_name = format_info.contract_name

    target_contract = slither.get_contract_from_name(contract_name)
    if not target_contract:
        raise SlitherException("Contract not found?!")
    for contract in [target_contract] + target_contract.derived_contracts:
        for function in contract.functions:
            for m  in function.modifiers:
                if (m.name == name):
                    in_file_str = slither.source_code[in_file].encode('utf-8')
                    old_str_of_interest = in_file_str[int(function.parameters_src.source_mapping['start']):
                                                      int(function.returns_src.source_mapping['start'])]
                    (new_str_of_interest, num_repl) = re.subn(name, name[0].lower()+name[1:],
                                                              old_str_of_interest.decode('utf-8'),1)
                    if num_repl != 0:
                        patch = {
                            "file" : in_file,
                            "detector" : "naming-convention (modifier uses)",
                            "start" : int(function.parameters_src.source_mapping['start']),
                            "end" : int(function.returns_src.source_mapping['start']),
                            "old_string" : old_str_of_interest.decode('utf-8'),
                            "new_string" : new_str_of_interest
                        }
                        if not patch in	patches[in_file_relative]:
                            patches[in_file_relative].append(patch)
                    else:
                        raise SlitherException("Could not find modifier name?!")


def _create_patch_function_definition(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative
    contract_name = format_info.contract_name
    modify_loc_start, modify_loc_end = format_info.loc_start, format_info.loc_end

    target_contract = slither.get_contract_from_name(contract_name)
    if not target_contract:
        raise SlitherException("Contract not found?!")
    for function in target_contract.functions:
        if function.name == name:
            in_file_str = slither.source_code[in_file].encode('utf-8')
            old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
            m = re.match(r'(.*)'+"function"+r'\s*'+name, old_str_of_interest.decode('utf-8'))
            old_str_of_interest = in_file_str[modify_loc_start:modify_loc_start+m.span()[1]]
            (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"function"+r'(.*)'+name, r'\1'+"function"+r'\2'+
                                                      name[0].lower()+name[1:], old_str_of_interest.decode('utf-8'), 1)
            if num_repl != 0:
                patch = {
                    "file" : in_file,
                    "detector" : "naming-convention (function definition)",
                    "start" : modify_loc_start,
                    "end" : modify_loc_start+m.span()[1],
                    "old_string" : old_str_of_interest.decode('utf-8'),
                    "new_string" : new_str_of_interest
                }
                if not patch in patches[in_file_relative]:
                    patches[in_file_relative].append(patch)
            else:
                raise SlitherException("Could not find function?!")


def _create_patch_function_calls(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative
    contract_name = format_info.contract_name

    for contract in slither.contracts:
        for function in contract.functions:
            for node in function.nodes:
                for high_level_call in node.high_level_calls:
                    if (high_level_call[0].name == contract_name and high_level_call[1].name == name):
                        for external_call in node.external_calls_as_expressions:
                            called_function = str(external_call.called).split('.')[-1]
                            if called_function == high_level_call[1].name:
                                in_file_str = slither.source_code[in_file].encode('utf-8')
                                old_str_of_interest = in_file_str[int(external_call.source_mapping['start']):
                                                                  int(external_call.source_mapping['start']) +
                                                                  int(external_call.source_mapping['length'])]
                                called_function_name = old_str_of_interest.decode('utf-8').split('.')[-1]
                                fixed_function_name = called_function_name[0].lower() + called_function_name[1:]
                                new_string = '.'.join(old_str_of_interest.decode('utf-8').split('.')[:-1]) + '.' + \
                                fixed_function_name
                                patch = {
                                    "file" : in_file,
                                    "detector" : "naming-convention (function calls)",
                                    "start" : external_call.source_mapping['start'],
                                    "end" : int(external_call.source_mapping['start']) +
                                    int(external_call.source_mapping['length']),
                                    "old_string" : old_str_of_interest.decode('utf-8'),
                                    "new_string" : new_string
                                }
                                if not patch in patches[in_file_relative]:
                                    patches[in_file_relative].append(patch)
                for internal_call in node.internal_calls_as_expressions:
                    if (str(internal_call.called) == name):
                        in_file_str = slither.source_code[in_file].encode('utf-8')
                        old_str_of_interest = in_file_str[int(internal_call.source_mapping['start']):
                                                          int(internal_call.source_mapping['start']) +
                                                          int(internal_call.source_mapping['length'])]
                        old_str_of_interest = old_str_of_interest.decode('utf-8').split('(')[0]
                        patch = {
                            "file" : in_file,
                            "detector" : "naming-convention (function calls)",
                            "start" : internal_call.source_mapping['start'],
                            "end" : int(internal_call.source_mapping['start']) +
                            int(internal_call.source_mapping['length']) -
                            len('('.join(in_file_str[int(internal_call.source_mapping['start']):
                                                     int(internal_call.source_mapping['start']) +
                                                     int(internal_call.source_mapping['length'])] \
                                         .decode('utf-8').split('(')[1:])) - 1,
                            "old_string" : old_str_of_interest,
                            "new_string" : old_str_of_interest[0].lower()+old_str_of_interest[1:]
                        }
                        if not patch in patches[in_file_relative]:
                            patches[in_file_relative].append(patch)


def _create_patch_event_definition(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative
    contract_name = format_info.contract_name
    modify_loc_start, modify_loc_end = format_info.loc_start, format_info.loc_end

    target_contract = slither.get_contract_from_name(contract_name)
    if not target_contract:
        raise SlitherException("Contract not found?!")
    for event in target_contract.events:
        if event.name == name:
            event_name = name.split('(')[0]
            in_file_str = slither.source_code[in_file].encode('utf-8')
            old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
            (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"event"+r'(.*)'+event_name, r'\1'+"event"+r'\2' +
                                                      event_name[0].capitalize()+event_name[1:],
                                                      old_str_of_interest.decode('utf-8'), 1)
            if num_repl != 0:
                patch = {
                    "file" : in_file,
                    "detector" : "naming-convention (event definition)",
                    "start" : modify_loc_start,
                    "end" : modify_loc_end,
                    "old_string" : old_str_of_interest.decode('utf-8'),
                    "new_string" : new_str_of_interest
                }
                if not patch in patches[in_file_relative]:
                    patches[in_file_relative].append(patch)
            else:
                raise SlitherException("Could not find event?!")


def _create_patch_event_calls(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative
    contract_name = format_info.contract_name

    event_name = name.split('(')[0]
    target_contract = slither.get_contract_from_name(contract_name)
    if not target_contract:
        raise SlitherException("Contract not found?!")
    for contract in [target_contract] + target_contract.derived_contracts:
        for function in contract.functions:
            for node in function.nodes:
                for call in node.internal_calls_as_expressions:
                    if (str(call.called) == event_name):
                        in_file_str = slither.source_code[in_file].encode('utf-8')
                        old_str_of_interest = in_file_str[int(call.source_mapping['start']):
                                                          int(call.source_mapping['start']) +
                                                          int(call.source_mapping['length'])]
                        patch = {
                            "file" : in_file,
                            "detector" : "naming-convention (event calls)",
                            "start" : call.source_mapping['start'],
                            "end" : int(call.source_mapping['start']) + int(call.source_mapping['length']),
                            "old_string" : old_str_of_interest.decode('utf-8'),
                            "new_string" : old_str_of_interest.decode('utf-8')[0].capitalize() +
                            old_str_of_interest.decode('utf-8')[1:]
                        }
                        if not patch in	patches[in_file_relative]:
                            patches[in_file_relative].append(patch)


def _create_patch_parameter_declaration(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative
    contract_name = format_info.contract_name
    modify_loc_start, modify_loc_end = format_info.loc_start, format_info.loc_end
    function_name = format_info.function_name

    target_contract = slither.get_contract_from_name(contract_name)
    if not target_contract:
        raise SlitherException("Contract not found?!")
    for function in target_contract.functions:
        if function.name == function_name:
            in_file_str = slither.source_code[in_file].encode('utf-8')
            old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
            if(name[0] == '_'):
                (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+name[0]+name[1].upper() +
                                                          name[2:]+r'\2', old_str_of_interest.decode('utf-8'), 1)
            else:
                (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+'_'+name[0].upper() +
                                                          name[1:]+r'\2', old_str_of_interest.decode('utf-8'), 1)
            if num_repl != 0:
                patch = {
                    "file" : in_file,
                    "detector" : "naming-convention (parameter declaration)",
                    "start" : modify_loc_start,
                    "end" : modify_loc_end,
                    "old_string" : old_str_of_interest.decode('utf-8'),
                    "new_string" : new_str_of_interest
                }
                if not patch in patches[in_file_relative]:
                    patches[in_file_relative].append(patch)
            else:
                raise SlitherException("Could not find parameter declaration?!")


def _create_patch_parameter_uses(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative
    contract_name = format_info.contract_name
    function_name = format_info.function_name

    for contract in slither.contracts:
        if (contract.name == contract_name):
            for function in contract.functions:
                if (function.name == function_name):
                    in_file_str = slither.source_code[in_file].encode('utf-8')
                    for node in function.nodes:
                        vars = node._expression_vars_written + node._expression_vars_read
                        for v in vars:
                            if isinstance(v, Identifier) and str(v) == name and [str(lv) for lv in
                                                                                 (node._local_vars_read +
                                                                                  node._local_vars_written)
                                                                                 if str(lv) == name]:
                                modify_loc_start = int(v.source_mapping['start'])
                                modify_loc_end = int(v.source_mapping['start']) + int(v.source_mapping['length'])
                                old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                                if(name[0] == '_'):
                                    (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)',
                                                                              r'\1'+name[0]+name[1].upper()+name[2:] +
                                                                              r'\2', old_str_of_interest.decode('utf-8'),
                                                                              1)
                                else:
                                    (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+'_' +
                                                                              name[0].upper()+name[1:]+r'\2',
                                                                              old_str_of_interest.decode('utf-8'), 1)
                                if num_repl != 0:
                                    patch = {
                                        "file" : in_file,
                                        "detector" : "naming-convention (parameter uses)",
                                        "start" : modify_loc_start,
                                        "end" : modify_loc_end,
                                        "old_string" : old_str_of_interest.decode('utf-8'),
                                        "new_string" : new_str_of_interest
                                    }
                                    if not patch in	patches[in_file_relative]:
                                        patches[in_file_relative].append(patch)
                                else:
                                    raise SlitherException("Could not find parameter use?!")

                    # Process function parameters passed to modifiers
                    for modifier in function._expression_modifiers:
                        for arg in modifier.arguments:
                            if str(arg) == name:
                                old_str_of_interest = in_file_str[modifier.source_mapping['start']:
                                                                  modifier.source_mapping['start'] +
                                                                  modifier.source_mapping['length']]
                                old_str_of_interest_beyond_modifier_name = old_str_of_interest.decode('utf-8')\
                                                                                              .split('(')[1]
                                if(name[0] == '_'):
                                    (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+name[0]+
                                                                              name[1].upper()+name[2:]+r'\2',
                                                                              old_str_of_interest_beyond_modifier_name, 1)
                                else:
                                    (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+'_'+
                                                                              name[0].upper()+name[1:]+r'\2',
                                                                              old_str_of_interest_beyond_modifier_name, 1)
                                if num_repl != 0:
                                    patch = {
                                        "file" : in_file,
                                        "detector" : "naming-convention (parameter uses)",
                                        "start" : modifier.source_mapping['start'] +
                                        len(old_str_of_interest.decode('utf-8').split('(')[0]) + 1,
                                        "end" : modifier.source_mapping['start'] + modifier.source_mapping['length'],
                                        "old_string" : old_str_of_interest_beyond_modifier_name,
                                        "new_string" : new_str_of_interest
                                    }
                                    if not patch in	patches[in_file_relative]:
                                        patches[in_file_relative].append(patch)
                                else:
                                    raise SlitherException("Could not find parameter use in modifier?!")


def _create_patch_state_variable_declaration(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative
    contract_name = format_info.contract_name
    modify_loc_start, modify_loc_end = format_info.loc_start, format_info.loc_end
    _target = format_info.target

    for contract in slither.contracts:
        if (contract.name == contract_name):
            for var in contract.state_variables:
                if (var.name == name):
                    in_file_str = slither.source_code[in_file].encode('utf-8')
                    old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                    m = re.search(name, old_str_of_interest.decode('utf-8'))
                    if (_target == "variable_constant"):
                        new_string = old_str_of_interest.decode('utf-8')[m.span()[0]:m.span()[1]].upper()
                    else:
                        new_string = old_str_of_interest.decode('utf-8')[m.span()[0]:m.span()[1]]
                        new_string = new_string[0].lower()+new_string[1:]
                    patch = {
                        "file" : in_file,
                        "detector" : "naming-convention (state variable declaration)",
                        "start" : modify_loc_start+m.span()[0],
                        "end" : modify_loc_start+m.span()[1],
                        "old_string" : old_str_of_interest.decode('utf-8')[m.span()[0]:m.span()[1]],
                        "new_string" : new_string
                    }
                    if not patch in	patches[in_file_relative]:
                        patches[in_file_relative].append(patch)


def _create_patch_state_variable_uses(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative
    contract_name = format_info.contract_name
    _target = format_info.target

    # To-do: Check cross-contract state variable uses
    for contract in slither.contracts:
        if (contract.name == contract_name):
            target_contract = contract
    for contract in slither.contracts:
        if (contract == target_contract or (contract in target_contract.derived_contracts)):
            fms = contract.functions + contract.modifiers
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
                            in_file_str = slither.source_code[in_file].encode('utf-8')
                            old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                            if (_target == "variable_constant"):
                                new_str_of_interest = old_str_of_interest.decode('utf-8').upper()
                            else:
                                new_str_of_interest = old_str_of_interest.decode('utf-8')
                                new_str_of_interest = new_str_of_interest[0].lower()+new_str_of_interest[1:]
                            patch = {
                                "file" : in_file,
                                "detector" : "naming-convention (state variable uses)",
                                "start" : modify_loc_start,
                                "end" : modify_loc_end,
                                "old_string" : old_str_of_interest.decode('utf-8'),
                                "new_string" : new_str_of_interest
                            }
                            if not patch in patches[in_file_relative]:
                                patches[in_file_relative].append(patch)


def _create_patch_enum_definition(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative
    contract_name = format_info.contract_name
    modify_loc_start, modify_loc_end = format_info.loc_start, format_info.loc_end

    for contract in slither.contracts:
        if (contract.name == contract_name):
            for enum in contract.enums:
                if (enum.name == name):
                    in_file_str = slither.source_code[in_file].encode('utf-8')
                    old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                    (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"enum"+r'(.*)'+name, r'\1'+"enum"+r'\2'+
                                                              name[0].capitalize()+name[1:],
                                                              old_str_of_interest.decode('utf-8'), 1)
                    if num_repl != 0:
                        patch = {
                            "file" : in_file,
                            "detector" : "naming-convention (enum definition)",
                            "start" : modify_loc_start,
                            "end" : modify_loc_end,
                            "old_string" : old_str_of_interest.decode('utf-8'),
                            "new_string" : new_str_of_interest
                        }
                        if not patch in patches[in_file_relative]:
                            patches[in_file_relative].append(patch)
                    else:
                        raise SlitherException("Could not find enum?!")


def _create_patch_enum_uses(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative
    contract_name = format_info.contract_name

    for contract in slither.contracts:
        if (contract.name == contract_name):
            target_contract = contract
    for contract in slither.contracts:
        if (contract == target_contract or (contract in target_contract.derived_contracts)):
            in_file_str = slither.source_code[in_file].encode('utf-8')
            # Check state variable declarations of enum type
            # To-do: Deep-check aggregate types (struct and mapping)
            svs = contract.variables
            for sv in svs:
                if (str(sv.type) == contract_name + "." + name):
                    old_str_of_interest = in_file_str[sv.source_mapping['start']:(sv.source_mapping['start']+
                                                                                  sv.source_mapping['length'])]
                    (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),
                                                              old_str_of_interest.decode('utf-8'), 1)
                    patch = {
                        "file" : in_file,
                        "detector" : "naming-convention (enum use)",
                        "start" : sv.source_mapping['start'],
                        "end" : sv.source_mapping['start'] + sv.source_mapping['length'],
                        "old_string" : old_str_of_interest.decode('utf-8'),
                        "new_string" : new_str_of_interest
                    }
                    if not patch in	patches[in_file_relative]:
                        patches[in_file_relative].append(patch)
            # Check function+modifier locals+parameters+returns
            # To-do: Deep-check aggregate types (struct and mapping)
            fms = contract.functions + contract.modifiers
            for fm in fms:
                # Enum declarations
                for v in fm.variables:
                    if (str(v.type) == contract_name + "." + name):
                        old_str_of_interest = in_file_str[v.source_mapping['start']:(v.source_mapping['start']+
                                                                                     v.source_mapping['length'])]
                        (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),
                                                                  old_str_of_interest.decode('utf-8'), 1)
                        patch = {
                            "file" : in_file,
                            "detector" : "naming-convention (enum use)",
                            "start" : v.source_mapping['start'],
                            "end" : v.source_mapping['start'] + v.source_mapping['length'],
                            "old_string" : old_str_of_interest.decode('utf-8'),
                            "new_string" : new_str_of_interest
                        }
                        if not patch in patches[in_file_relative]:
                            patches[in_file_relative].append(patch)
            # Capture enum uses such as "num = numbers.ONE;"
            for function in contract.functions:
                for node in function.nodes:
                    for ir in node.irs:
                        if isinstance(ir, Member):
                            if str(ir.variable_left) == name:
                                old_str_of_interest = in_file_str[node.source_mapping['start']:
                                                                  (node.source_mapping['start']+
                                                                   node.source_mapping['length'])].decode('utf-8')\
                                                                   .split('=')[1]
                                m = re.search(r'(.*)'+name, old_str_of_interest)
                                old_str_of_interest = old_str_of_interest[m.span()[0]:]
                                (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name, r'\1'+name[0].upper()+name[1:],
                                                                          old_str_of_interest, 1)
                                if num_repl != 0:
                                    patch = {
                                        "file" : in_file,
                                        "detector" : "naming-convention (enum use)",
                    "start" : node.source_mapping['start'] +
                                        len(in_file_str[node.source_mapping['start']:
                                                        (node.source_mapping['start']+
                                                         node.source_mapping['length'])].decode('utf-8').split('=')[0]) +
                                        1 + m.span()[0],
                                        "end" : node.source_mapping['start'] +
                                        len(in_file_str[node.source_mapping['start']:(node.source_mapping['start']+
                                                                                      node.source_mapping['length'])].\
                                            decode('utf-8').split('=')[0]) + 1 + m.span()[0] + len(old_str_of_interest),
                                        "old_string" : old_str_of_interest,
                                        "new_string" : new_str_of_interest
                                    }
                                    if not patch in	patches[in_file_relative]:
                                        patches[in_file_relative].append(patch)
                                else:
                                    raise SlitherException("Could not find new object?!")
            # To-do: Check any other place/way where enum type is used


def _create_patch_struct_definition(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative
    contract_name = format_info.contract_name
    modify_loc_start, modify_loc_end = format_info.loc_start, format_info.loc_end

    for contract in slither.contracts:
        if (contract.name == contract_name):
            for struct in contract.structures:
                if (struct.name == name):
                    in_file_str = slither.source_code[in_file].encode('utf-8')
                    old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                    (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"struct"+r'(.*)'+name, r'\1'+"struct"+r'\2'+
                                                              name[0].capitalize()+name[1:],
                                                              old_str_of_interest.decode('utf-8'), 1)
                    if num_repl != 0:
                        patch = {
                            "file" : in_file,
                            "detector" : "naming-convention (struct definition)",
                            "start" : modify_loc_start,
                            "end" : modify_loc_end,
                            "old_string" : old_str_of_interest.decode('utf-8'),
                            "new_string" : new_str_of_interest
                        }
                        if not patch in patches[in_file_relative]:
                            patches[in_file_relative].append(patch)
                    else:
                        raise SlitherException("Could not find struct?!")


def _create_patch_struct_uses(format_info):
    slither, patches, name = format_info.slither, format_info.patches, format_info.name
    in_file, in_file_relative = format_info.in_file, format_info.in_file_relative
    contract_name = format_info.contract_name

    for contract in slither.contracts:
        if (contract.name == contract_name):
            target_contract = contract
    for contract in slither.contracts:
        if (contract == target_contract or (contract in target_contract.derived_contracts)):
            in_file_str = slither.source_code[in_file].encode('utf-8')
            # Check state variables of struct type
            # To-do: Deep-check aggregate types (struct and mapping)
            svs = contract.variables
            for sv in svs:
                if (str(sv.type) == contract_name + "." + name):
                    old_str_of_interest = in_file_str[sv.source_mapping['start']:(sv.source_mapping['start']+
                                                                                  sv.source_mapping['length'])]
                    (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),
                                                              old_str_of_interest.decode('utf-8'), 1)
                    patch = {
                        "file" : in_file,
                        "detector" : "naming-convention (struct use)",
                        "start" : sv.source_mapping['start'],
                        "end" : sv.source_mapping['start'] + sv.source_mapping['length'],
                        "old_string" : old_str_of_interest.decode('utf-8'),
                        "new_string" : new_str_of_interest
                    }
                    if not patch in patches[in_file_relative]:
                        patches[in_file_relative].append(patch)
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
                        patch = {
                            "file" : in_file,
                            "detector" : "naming-convention (struct use)",
                            "start" : v.source_mapping['start'],
                            "end" : v.source_mapping['start'] + v.source_mapping['length'],
                            "old_string" : old_str_of_interest.decode('utf-8'),
                            "new_string" : new_str_of_interest
                        }
                        if not patch in patches[in_file_relative]:
                            patches[in_file_relative].append(patch)
            # To-do: Check any other place/way where struct type is used (e.g. typecast)
