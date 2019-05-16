import re, sys
from slither.core.expressions.identifier import Identifier
from slither.core.cfg.node import Node
from slither.slithir.operations import NewContract
from slither.slithir.operations import Member

class FormatNamingConvention:

    @staticmethod
    def format(slither, patches, elements):
        for element in elements:
            if (element['additional_fields']['target'] == "parameter"):
                FormatNamingConvention.create_patch(slither, patches, element['additional_fields']['target'], element['name'], element['function']['name'], element['function']['contract']['name'], element['source_mapping']['filename_absolute'],element['source_mapping']['start'],(element['source_mapping']['start']+element['source_mapping']['length']))
            elif (element['additional_fields']['target'] == "modifier" or element['additional_fields']['target'] == "function" or element['additional_fields']['target'] == "event" or element['additional_fields']['target'] == "variable" or element['additional_fields']['target'] == "variable_constant" or element['additional_fields']['target'] == "enum" or element['additional_fields']['target'] == "structure"):
                FormatNamingConvention.create_patch(slither, patches, element['additional_fields']['target'], element['name'], element['name'], element['contract']['name'], element['source_mapping']['filename_absolute'],element['source_mapping']['start'],(element['source_mapping']['start']+element['source_mapping']['length']))
            else:
                FormatNamingConvention.create_patch(slither, patches, element['additional_fields']['target'], element['name'], element['name'], element['name'], element['source_mapping']['filename_absolute'],element['source_mapping']['start'],(element['source_mapping']['start']+element['source_mapping']['length']))

    @staticmethod
    def create_patch(slither, patches, _target, name, function_name, contract_name, in_file, modify_loc_start, modify_loc_end):
        if _target == "contract":
            FormatNamingConvention.create_patch_contract_definition(slither, patches, name, in_file, modify_loc_start, modify_loc_end)
            FormatNamingConvention.create_patch_contract_uses(slither, patches, name, in_file)
        elif _target == "structure":
            FormatNamingConvention.create_patch_struct_definition(slither, patches, name, contract_name, in_file, modify_loc_start, modify_loc_end)
            FormatNamingConvention.create_patch_struct_uses(slither, patches, name, contract_name, in_file)
        elif _target == "event":
            FormatNamingConvention.create_patch_event_definition(slither, patches, name, contract_name, in_file, modify_loc_start, modify_loc_end)
            FormatNamingConvention.create_patch_event_calls(slither, patches, name, contract_name, in_file)
        elif _target == "function":
            if name != contract_name:
                FormatNamingConvention.create_patch_function_definition(slither, patches, name, contract_name, in_file, modify_loc_start, modify_loc_end)
                FormatNamingConvention.create_patch_function_calls(slither, patches, name, contract_name, in_file)
        elif _target == "parameter":
            FormatNamingConvention.create_patch_parameter_declaration(slither, patches, name, function_name, contract_name, in_file, modify_loc_start, modify_loc_end)
            FormatNamingConvention.create_patch_parameter_uses(slither, patches, name, function_name, contract_name, in_file)
        elif _target == "variable_constant" or _target == "variable":
            FormatNamingConvention.create_patch_state_variable_declaration(slither, patches, _target, name, contract_name, in_file, modify_loc_start, modify_loc_end)
            FormatNamingConvention.create_patch_state_variable_uses(slither, patches, _target, name, contract_name, in_file)
        elif _target == "enum":
            FormatNamingConvention.create_patch_enum_definition(slither, patches, name, contract_name, in_file, modify_loc_start, modify_loc_end)
            FormatNamingConvention.create_patch_enum_uses(slither, patches, name, contract_name, in_file)
        elif _target == "modifier":
            FormatNamingConvention.create_patch_modifier_definition(slither, patches, name, contract_name, in_file, modify_loc_start, modify_loc_end)
            FormatNamingConvention.create_patch_modifier_uses(slither, patches, name, contract_name, in_file)
        else:
            print("Unknown naming convention! " + _target)
            sys.exit(-1)
        
    @staticmethod
    def create_patch_contract_definition(slither, patches, name, in_file, modify_loc_start, modify_loc_end):
        for contract in slither.contracts:
            if contract.name == name:
                in_file_str = slither.source_code[in_file]
                old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                m = re.match(r'(.*)'+"contract"+r'(.*)'+name, old_str_of_interest)
                old_str_of_interest = in_file_str[modify_loc_start:modify_loc_start+m.span()[1]]
                (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"contract"+r'(.*)'+name, r'\1'+"contract"+r'\2'+name.capitalize(), old_str_of_interest, 1)
                if num_repl != 0:
                    patch = {
                        "detector" : "naming-convention (contract definition)",
                        "start":modify_loc_start,
                        "end":modify_loc_start+m.span()[1],
                        "old_string":old_str_of_interest,
                        "new_string":new_str_of_interest
                    }
                    if not patch in patches[in_file]:
                        patches[in_file].append(patch)
                else:
                    print("Error: Could not find contract?!")
                    sys.exit(-1)
                    
    @staticmethod
    def create_patch_contract_uses(slither, patches, name, in_file):
        for contract in slither.contracts:
            if contract.name != name:
                in_file_str = slither.source_code[in_file]
                # Check state variables of contract type
                # To-do: Deep-check aggregate types (struct and mapping)
                svs = contract.variables
                for sv in svs:
                    if (str(sv.type) == name):
                        old_str_of_interest = in_file_str[sv.source_mapping['start']:(sv.source_mapping['start']+sv.source_mapping['length'])]
                        (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),old_str_of_interest, 1)
                        patch = {
                            "detector" : "naming-convention (contract state variable)",
                            "start" : sv.source_mapping['start'],
                            "end" : sv.source_mapping['start'] + sv.source_mapping['length'],
                            "old_string" : old_str_of_interest,
                            "new_string" : new_str_of_interest
                        }
                        if not patch in patches[in_file]:
                            patches[in_file].append(patch)
                # Check function+modifier locals+parameters+returns
                # To-do: Deep-check aggregate types (struct and mapping)
                fms = contract.functions + contract.modifiers
                for fm in fms:
                    for v in fm.variables:
                        if (str(v.type) == name):
                            old_str_of_interest = in_file_str[v.source_mapping['start']:(v.source_mapping['start']+v.source_mapping['length'])]
                            (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),old_str_of_interest, 1)
                            patch = {
                                "detector" : "naming-convention (contract function variable)",
                                "start" : v.source_mapping['start'],
                                "end" : v.source_mapping['start'] + v.source_mapping['length'],
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            }
                            if not patch in patches[in_file]:
                                patches[in_file].append(patch)
                # Check "new" expressions for creation of contract objects
                for function in contract.functions:
                    for node in function.nodes:
                        for ir in node.irs:
                            if isinstance(ir, NewContract) and ir.contract_name == name:
                                old_str_of_interest = in_file_str[node.source_mapping['start']:node.source_mapping['start'] + node.source_mapping['length']]
                                m = re.search("new"+r'(.*)'+name, old_str_of_interest)
                                old_str_of_interest = old_str_of_interest[m.span()[0]:]
                                (new_str_of_interest, num_repl) = re.subn("new"+r'(.*)'+name, "new"+r'\1'+name[0].upper()+name[1:], old_str_of_interest, 1)
                                if num_repl != 0:
                                    patch = {
                                        "detector" : "naming-convention (contract new object)",
                                        "start" : node.source_mapping['start'] + m.span()[0],
                                        "end" : node.source_mapping['start'] + m.span()[1],
                                        "old_string" : old_str_of_interest,
                                        "new_string" : new_str_of_interest
                                    }
                                    if not patch in patches[in_file]:
                                        patches[in_file].append(patch)
                                else:
                                    print("Error: Could not find new object?!")
                                    sys.exit(-1)

            else:
                # Ignore contract definition
                continue
            
    @staticmethod
    def create_patch_modifier_definition(slither, patches, name, contract_name, in_file, modify_loc_start, modify_loc_end):
        for contract in slither.contracts:
            if contract.name == contract_name:
                for modifier in contract.modifiers:
                    if modifier.name == name:
                        in_file_str = slither.source_code[in_file]
                        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                        m = re.match(r'(.*)'+"modifier"+r'(.*)'+name, old_str_of_interest)
                        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_start+m.span()[1]]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"modifier"+r'(.*)'+name, r'\1'+"modifier"+r'\2'+name[0].lower()+name[1:], old_str_of_interest, 1)
                        if num_repl != 0:
                            patch = {
                                "detector" : "naming-convention (modifier definition)",
                                "start" : modify_loc_start,
                                "end" : modify_loc_start+m.span()[1],
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            }
                            if not patch in patches[in_file]:
                                patches[in_file].append(patch)
                        else:
                            print("Error: Could not find modifier?!")
                            sys.exit(-1)
                            
    @staticmethod
    def create_patch_modifier_uses(slither, patches, name, contract_name, in_file):
        for contract in slither.contracts:
            if contract.name == contract_name:
                for function in contract.functions:
                    for m  in function.modifiers:
                        if (m.name == name):
                            in_file_str = slither.source_code[in_file]
                            old_str_of_interest = in_file_str[int(function.parameters_src.source_mapping['start']):int(function.returns_src.source_mapping['start'])]
                            (new_str_of_interest, num_repl) = re.subn(name, name[0].lower()+name[1:],old_str_of_interest,1)
                            if num_repl != 0:
                                patch = {
                                    "detector" : "naming-convention (modifier uses)",
                                    "start" : int(function.parameters_src.source_mapping['start']),
                                    "end" : int(function.returns_src.source_mapping['start']),
                                    "old_string" : old_str_of_interest,
                                    "new_string" : new_str_of_interest
                                }
                                if not patch in	patches[in_file]:
                                    patches[in_file].append(patch)
                            else:
                                print("Error: Could not find modifier name?!")
                                sys.exit(-1)
                                
    @staticmethod
    def create_patch_function_definition(slither, patches, name, contract_name, in_file, modify_loc_start, modify_loc_end):
        for contract in slither.contracts:
            if contract.name == contract_name:
                for function in contract.functions:
                    if function.name == name:
                        in_file_str = slither.source_code[in_file]
                        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                        m = re.match(r'(.*)'+"function"+r'(.*)'+name, old_str_of_interest)
                        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_start+m.span()[1]]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"function"+r'(.*)'+name, r'\1'+"function"+r'\2'+name[0].lower()+name[1:], old_str_of_interest, 1)
                        if num_repl != 0:
                            patch = {
                                "detector" : "naming-convention (function definition)",
                                "start" : modify_loc_start,
                                "end" : modify_loc_start+m.span()[1],
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            }
                            if not patch in patches[in_file]:
                                patches[in_file].append(patch)
                        else:
                            print("Error: Could not find function?!")
                            sys.exit(-1)
                            
    @staticmethod
    def create_patch_function_calls(slither, patches, name, contract_name, in_file):
        for contract in slither.contracts:
            for function in contract.functions:
                for node in function.nodes:
                    for high_level_call in node.high_level_calls:
                        if (high_level_call[0].name == contract_name and high_level_call[1].name == name):                    
                            for external_call in node.external_calls_as_expressions:
                                called_function = str(external_call.called).split('.')[-1]
                                if called_function == high_level_call[1].name:
                                    in_file_str = slither.source_code[in_file]
                                    old_str_of_interest = in_file_str[int(external_call.source_mapping['start']):int(external_call.source_mapping['start'])+int(external_call.source_mapping['length'])]
                                    called_function_name = old_str_of_interest.split('.')[-1]
                                    fixed_function_name = called_function_name[0].lower() + called_function_name[1:]
                                    new_string = '.'.join(old_str_of_interest.split('.')[:-1]) + '.' + fixed_function_name
                                    patch = {
                                        "detector" : "naming-convention (function calls)",
                                        "start" : external_call.source_mapping['start'],
                                        "end" : int(external_call.source_mapping['start']) + int(external_call.source_mapping['length']),
                                        "old_string" : old_str_of_interest,
                                        "new_string" : new_string
                                    }
                                    if not patch in patches[in_file]:
                                        patches[in_file].append(patch)
                    for internal_call in node.internal_calls_as_expressions:
                        if (str(internal_call.called) == name):
                            in_file_str = slither.source_code[in_file]
                            old_str_of_interest = in_file_str[int(internal_call.source_mapping['start']):int(internal_call.source_mapping['start'])+int(internal_call.source_mapping['length'])]
                            patch = {
                                "detector" : "naming-convention (function calls)",
                                "start" : internal_call.source_mapping['start'],
                                "end" : int(internal_call.source_mapping['start']) + int(internal_call.source_mapping['length']),
                                "old_string" : old_str_of_interest,
                                "new_string" : old_str_of_interest[0].lower()+old_str_of_interest[1:]
                            }
                            if not patch in patches[in_file]:
                                patches[in_file].append(patch)
                            
    @staticmethod
    def create_patch_event_definition(slither, patches, name, contract_name, in_file, modify_loc_start, modify_loc_end):
        for contract in slither.contracts:
            if contract.name == contract_name:
                for event in contract.events:
                    if event.name == name:
                        event_name = name.split('(')[0]
                        in_file_str = slither.source_code[in_file]
                        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"event"+r'(.*)'+event_name, r'\1'+"event"+r'\2'+event_name[0].capitalize()+event_name[1:], old_str_of_interest, 1)
                        if num_repl != 0:
                            patch = {
                                "detector" : "naming-convention (event definition)",
                                "start" : modify_loc_start,
                                "end" : modify_loc_end,
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            }
                            if not patch in patches[in_file]:
                                patches[in_file].append(patch)
                        else:
                            print("Error: Could not find event?!")
                            sys.exit(-1)
                            
    @staticmethod
    def create_patch_event_calls(slither, patches, name, contract_name, in_file):
        event_name = name.split('(')[0]
        for contract in slither.contracts:
            if (contract.name == contract_name):
                for function in contract.functions:
                    for node in function.nodes:
                        for call in node.internal_calls_as_expressions:
                            if (str(call.called) == event_name):
                                in_file_str = slither.source_code[in_file]
                                old_str_of_interest = in_file_str[int(call.source_mapping['start']):int(call.source_mapping['start'])+int(call.source_mapping['length'])]
                                patch = {
                                    "detector" : "naming-convention (event calls)",
                                    "start" : call.source_mapping['start'],
                                    "end" : int(call.source_mapping['start']) + int(call.source_mapping['length']),
                                    "old_string" : old_str_of_interest,
                                    "new_string" : old_str_of_interest[0].capitalize()+old_str_of_interest[1:]
                                }
                                if not patch in	patches[in_file]:
                                    patches[in_file].append(patch)
                                
    @staticmethod
    def create_patch_parameter_declaration(slither, patches, name, function_name, contract_name, in_file, modify_loc_start, modify_loc_end):
        for contract in slither.contracts:
            if contract.name == contract_name:
                for function in contract.functions:
                    if function.name == function_name:
                        in_file_str = slither.source_code[in_file]
                        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                        if(name[0] == '_'):
                            (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+name[0]+name[1].upper()+name[2:]+r'\2', old_str_of_interest, 1)
                        else:
                            (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+'_'+name[0].upper()+name[1:]+r'\2', old_str_of_interest, 1)
                        if num_repl != 0:
                            patch = {
                                "detector" : "naming-convention (parameter declaration)",
                                "start" : modify_loc_start,
                                "end" : modify_loc_end,
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            }
                            if not patch in patches[in_file]:
                                patches[in_file].append(patch)
                        else:
                            print("Error: Could not find parameter?!")
                            sys.exit(-1)

    @staticmethod                        
    def create_patch_parameter_uses(slither, patches, name, function_name, contract_name, in_file):
        for contract in slither.contracts:
            if (contract.name == contract_name):
                for function in contract.functions:
                    if (function.name == function_name):
                        in_file_str = slither.source_code[in_file]
                        for node in function.nodes:
                            vars = node._expression_vars_written + node._expression_vars_read
                            for v in vars:
                                if isinstance(v, Identifier) and str(v) == name and [str(lv) for lv in (node._local_vars_read+node._local_vars_written) if str(lv) == name]:
                                    modify_loc_start = int(v.source_mapping['start'])
                                    modify_loc_end = int(v.source_mapping['start']) + int(v.source_mapping['length'])
                                    old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                                    if(name[0] == '_'):
                                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+name[0]+name[1].upper()+name[2:]+r'\2', old_str_of_interest, 1)
                                    else:
                                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+'_'+name[0].upper()+name[1:]+r'\2', old_str_of_interest, 1)
                                    if num_repl != 0:
                                        patch = {
                                            "detector" : "naming-convention (parameter uses)",
                                            "start" : modify_loc_start,
                                            "end" : modify_loc_end,
                                            "old_string" : old_str_of_interest,
                                            "new_string" : new_str_of_interest
                                        }
                                        if not patch in	patches[in_file]:
                                            patches[in_file].append(patch)
                                    else:
                                        print("Error: Could not find parameter?!")
                                        sys.exit(-1)
                        # Process function parameters passed to modifiers
                        for modifier in function._expression_modifiers:
                            for arg in modifier.arguments:
                                if str(arg) == name:
                                    old_str_of_interest = in_file_str[modifier.source_mapping['start']:modifier.source_mapping['start']+modifier.source_mapping['length']]
                                    old_str_of_interest_beyond_modifier_name = old_str_of_interest.split('(')[1]
                                    if(name[0] == '_'):
                                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+name[0]+name[1].upper()+name[2:]+r'\2', old_str_of_interest_beyond_modifier_name, 1)
                                    else:
                                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name+r'(.*)', r'\1'+'_'+name[0].upper()+name[1:]+r'\2', old_str_of_interest_beyond_modifier_name, 1)
                                    if num_repl != 0:
                                        patch = {
                                            "detector" : "naming-convention (parameter uses)",
                                            "start" : modifier.source_mapping['start'] + len(old_str_of_interest.split('(')[0]) + 1,
                                            "end" : modifier.source_mapping['start'] + modifier.source_mapping['length'],
                                            "old_string" : old_str_of_interest_beyond_modifier_name,
                                            "new_string" : new_str_of_interest
                                        }
                                        if not patch in	patches[in_file]:
                                            patches[in_file].append(patch)
                                    else:
                                        print("Error: Could not find parameter?!")
                                        sys.exit(-1)

    @staticmethod
    def create_patch_state_variable_declaration(slither, patches, _target, name, contract_name, in_file, modify_loc_start, modify_loc_end):
        for contract in slither.contracts:
            if (contract.name == contract_name):
                for var in contract.state_variables:
                    if (var.name == name):
                        in_file_str = slither.source_code[in_file]
                        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                        m = re.search(name, old_str_of_interest)
                        if (_target == "variable_constant"):
                            new_string = old_str_of_interest[m.span()[0]:m.span()[1]].upper()
                        else:
                            new_string = old_str_of_interest[m.span()[0]:m.span()[1]]
                            new_string = new_string[0].lower()+new_string[1:]
                        patch = {
                            "detector" : "naming-convention (state variable declaration)",
                            "start" : modify_loc_start+m.span()[0],
                            "end" : modify_loc_start+m.span()[1],
                            "old_string" : old_str_of_interest[m.span()[0]:m.span()[1]],
                            "new_string" : new_string 
                        }
                        if not patch in	patches[in_file]:
                            patches[in_file].append(patch)
                        
    @staticmethod
    def create_patch_state_variable_uses(slither, patches, _target, name, contract_name, in_file):
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
                            if isinstance(v, Identifier) and str(v) == name and [str(sv) for sv in (node._state_vars_read+node._state_vars_written) if str(sv) == name]:
                                modify_loc_start = int(v.source_mapping['start'])
                                modify_loc_end = int(v.source_mapping['start']) + int(v.source_mapping['length'])
                                in_file_str = slither.source_code[in_file]
                                old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                                if (_target == "variable_constant"):
                                    new_str_of_interest = old_str_of_interest.upper()
                                else:
                                    new_str_of_interest = old_str_of_interest
                                    new_str_of_interest = new_str_of_interest[0].lower()+new_str_of_interest[1:]
                                patch = {
                                    "detector" : "naming-convention (state variable uses)",
                                    "start" : modify_loc_start,
                                    "end" : modify_loc_end,
                                    "old_string" : old_str_of_interest,
                                    "new_string" : new_str_of_interest
                                }
                                if not patch in patches[in_file]:
                                    patches[in_file].append(patch)

    @staticmethod                                
    def create_patch_enum_definition(slither, patches, name, contract_name, in_file, modify_loc_start, modify_loc_end):
        for contract in slither.contracts:
            if (contract.name == contract_name):
                for enum in contract.enums:
                    if (enum.name == name):
                        in_file_str = slither.source_code[in_file]
                        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"enum"+r'(.*)'+name, r'\1'+"enum"+r'\2'+name[0].capitalize()+name[1:], old_str_of_interest, 1)
                        if num_repl != 0:
                            patch = {
                                "detector" : "naming-convention (enum definition)",
                                "start" : modify_loc_start,
                                "end" : modify_loc_end,
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            }
                            if not patch in patches[in_file]:
                                patches[in_file].append(patch)
                        else:
                            print("Error: Could not find enum?!")
                            sys.exit(-1)
                            
    @staticmethod
    def create_patch_enum_uses(slither, patches, name, contract_name, in_file):
        for contract in slither.contracts:
            if contract.name == contract_name:
                in_file_str = slither.source_code[in_file]
                # Check state variable declarations of enum type
                # To-do: Deep-check aggregate types (struct and mapping)
                svs = contract.variables
                for sv in svs:
                    if (str(sv.type) == contract_name + "." + name):
                        old_str_of_interest = in_file_str[sv.source_mapping['start']:(sv.source_mapping['start']+sv.source_mapping['length'])]
                        (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),old_str_of_interest, 1)
                        patch = {
                            "detector" : "naming-convention (enum use)",
                            "start" : sv.source_mapping['start'],
                            "end" : sv.source_mapping['start'] + sv.source_mapping['length'],
                            "old_string" : old_str_of_interest,
                            "new_string" : new_str_of_interest
                        }
                        if not patch in	patches[in_file]:
                            patches[in_file].append(patch)
                # Check function+modifier locals+parameters+returns
                # To-do: Deep-check aggregate types (struct and mapping)
                fms = contract.functions + contract.modifiers
                for fm in fms:
                    # Enum declarations
                    for v in fm.variables:
                        if (str(v.type) == contract_name + "." + name):
                            old_str_of_interest = in_file_str[v.source_mapping['start']:(v.source_mapping['start']+v.source_mapping['length'])]
                            (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),old_str_of_interest, 1)
                            patch = {
                                "detector" : "naming-convention (enum use)",
                                "start" : v.source_mapping['start'],
                                "end" : v.source_mapping['start'] + v.source_mapping['length'],
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            }
                            if not patch in patches[in_file]:
                                patches[in_file].append(patch)
                # Capture enum uses such as "num = numbers.ONE;"
                for function in contract.functions:
                    for node in function.nodes:
                        for ir in node.irs:
                            if isinstance(ir, Member):
                                if str(ir.variable_left) == name:
                                    old_str_of_interest = in_file_str[node.source_mapping['start']:(node.source_mapping['start']+node.source_mapping['length'])].split('=')[1]
                                    m = re.search(r'(.*)'+name, old_str_of_interest)
                                    old_str_of_interest = old_str_of_interest[m.span()[0]:]
                                    (new_str_of_interest, num_repl) = re.subn(r'(.*)'+name, r'\1'+name[0].upper()+name[1:], old_str_of_interest, 1)
                                    if num_repl != 0:
                                        patch = {
                                            "detector" : "naming-convention (enum use)",
					    "start" : node.source_mapping['start'] + len(in_file_str[node.source_mapping['start']:(node.source_mapping['start']+node.source_mapping['length'])].split('=')[0]) + 1 + m.span()[0],
                                            "end" : node.source_mapping['start'] + len(in_file_str[node.source_mapping['star\
t']:(node.source_mapping['start']+node.source_mapping['length'])].split('=')[0]) + 1 + m.span()[0] + len(old_str_of_interest),
                                            "old_string" : old_str_of_interest,
                                            "new_string" : new_str_of_interest
                                        }
                                        if not patch in	patches[in_file]:
                                            patches[in_file].append(patch)
                                    else:
                                        print("Error: Could not find new object?!")
                                        sys.exit(-1)
                # To-do: Check any other place/way where enum type is used

    @staticmethod            
    def create_patch_struct_definition(slither, patches, name, contract_name, in_file, modify_loc_start, modify_loc_end):
        for contract in slither.contracts:
            if (contract.name == contract_name):
                for struct in contract.structures:
                    if (struct.name == name):
                        in_file_str = slither.source_code[in_file]
                        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"struct"+r'(.*)'+name, r'\1'+"struct"+r'\2'+name[0].capitalize()+name[1:], old_str_of_interest, 1)
                        if num_repl != 0:
                            patch = {
                                "detector" : "naming-convention (struct definition)",
                                "start" : modify_loc_start,
                                "end" : modify_loc_end,
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            }
                            if not patch in patches[in_file]:
                                patches[in_file].append(patch)
                        else:
                            print("Error: Could not find struct?!")
                            sys.exit(-1)

    @staticmethod                            
    def create_patch_struct_uses(slither, patches, name, contract_name, in_file):
        for contract in slither.contracts:
            if (contract.name == contract_name):
                target_contract = contract
        for contract in slither.contracts:
            if (contract == target_contract or (contract in target_contract.derived_contracts)):
                in_file_str = slither.source_code[in_file]
                # Check state variables of struct type
                # To-do: Deep-check aggregate types (struct and mapping)
                svs = contract.variables
                for sv in svs:
                    if (str(sv.type) == contract_name + "." + name):
                        old_str_of_interest = in_file_str[sv.source_mapping['start']:(sv.source_mapping['start']+sv.source_mapping['length'])]
                        (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),old_str_of_interest, 1)
                        patch = {
                            "detector" : "naming-convention (struct use)",
                            "start" : sv.source_mapping['start'],
                            "end" : sv.source_mapping['start'] + sv.source_mapping['length'],
                            "old_string" : old_str_of_interest,
                            "new_string" : new_str_of_interest
                        }
                        if not patch in patches[in_file]:
                            patches[in_file].append(patch)
                # Check function+modifier locals+parameters+returns
                # To-do: Deep-check aggregate types (struct and mapping)
                fms = contract.functions + contract.modifiers
                for fm in fms:
                    for v in fm.variables:
                        if (str(v.type) == contract_name + "." + name):
                            old_str_of_interest = in_file_str[v.source_mapping['start']:(v.source_mapping['start']+v.source_mapping['length'])]
                            (new_str_of_interest, num_repl) = re.subn(name, name.capitalize(),old_str_of_interest, 1)
                            patch = {
                                "detector" : "naming-convention (struct use)",
                                "start" : v.source_mapping['start'],
                                "end" : v.source_mapping['start'] + v.source_mapping['length'],
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            }
                            if not patch in	patches[in_file]:
                                patches[in_file].append(patch)
                # To-do: Check any other place/way where struct type is used (e.g. typecast)
