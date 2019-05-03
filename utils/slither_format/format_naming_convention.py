import re
from slither.core.expressions.identifier import Identifier

class FormatNamingConvention:

    @staticmethod
    def format(slither, patches, elements):
        for element in elements:
            if (element['target'] == "parameter"):
                FormatNamingConvention.create_patch(slither, patches, element['target'], element['name'], element['function'], element['contract'], element['source_mapping']['filename'],element['source_mapping']['start'],(element['source_mapping']['start']+element['source_mapping']['length']))
            elif (element['target'] == "modifier" or element['target'] == "function" or element['target'] == "event" or element['target'] == "variable" or element['target'] == "variable_constant" or element['target'] == "enum" or element['target'] == "structure"):
                FormatNamingConvention.create_patch(slither, patches, element['target'], element['name'], element['name'], element['contract'], element['source_mapping']['filename'],element['source_mapping']['start'],(element['source_mapping']['start']+element['source_mapping']['length']))
            else:
                FormatNamingConvention.create_patch(slither, patches, element['target'], element['name'], element['name'], element['name'], element['source_mapping']['filename'],element['source_mapping']['start'],(element['source_mapping']['start']+element['source_mapping']['length']))

    @staticmethod
    def create_patch(_slither, patches, _target, _name, _function_name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
        if _target == "contract":
            FormatNamingConvention.create_patch_contract_definition(_slither, patches, _name, _in_file, _modify_loc_start, _modify_loc_end)
            FormatNamingConvention.create_patch_contract_uses(_slither, patches, _name, _in_file)
        elif _target == "structure":
            FormatNamingConvention.create_patch_struct_definition(_slither, patches, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
            FormatNamingConvention.create_patch_struct_uses(_slither, patches, _name, _contract_name, _in_file)
        elif _target == "event":
            FormatNamingConvention.create_patch_event_definition(_slither, patches, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
            FormatNamingConvention.create_patch_event_calls(_slither, patches, _name, _contract_name, _in_file)
        elif _target == "function":
            FormatNamingConvention.create_patch_function_definition(_slither, patches, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
            FormatNamingConvention.create_patch_function_calls(_slither, patches, _name, _contract_name, _in_file)
        elif _target == "parameter":
            FormatNamingConvention.create_patch_parameter_declaration(_slither, patches, _name, _function_name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
            FormatNamingConvention.create_patch_parameter_uses(_slither, patches, _name, _function_name, _contract_name, _in_file)
        elif _target == "variable_constant" or _target == "variable":
            FormatNamingConvention.create_patch_state_variable_declaration(_slither, patches, _target, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
            FormatNamingConvention.create_patch_state_variable_uses(_slither, patches, _target, _name, _contract_name, _in_file)
        elif _target == "enum":
            FormatNamingConvention.create_patch_enum_definition(_slither, patches, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
            FormatNamingConvention.create_patch_enum_uses(_slither, patches, _name, _contract_name, _in_file)
        elif _target == "modifier":
            FormatNamingConvention.create_patch_modifier_definition(_slither, patches, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end)
            FormatNamingConvention.create_patch_modifier_uses(_slither, patches, _name, _contract_name, _in_file)
        else:
            print("Unknown naming convention! " + _target)
            sys.exit(-1)
        
    @staticmethod
    def create_patch_contract_definition(_slither, patches, _name, _in_file, _modify_loc_start, _modify_loc_end):
        for contract in _slither.contracts_derived:
            if contract.name == _name:
                in_file_str = _slither.source_code[_in_file]
                old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                m = re.match(r'(.*)'+"contract"+r'(.*)'+_name, old_str_of_interest)
                old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_start+m.span()[1]]
                (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"contract"+r'(.*)'+_name, r'\1'+"contract"+r'\2'+_name.capitalize(), old_str_of_interest, 1)
                if num_repl != 0:
                    patches[_in_file].append({
                        "detector" : "naming-convention (contract definition)",
                        "start":_modify_loc_start,
                        "end":_modify_loc_start+m.span()[1],
                        "old_string":old_str_of_interest,
                        "new_string":new_str_of_interest
                    })
                else:
                    print("Error: Could not find contract?!")
                    sys.exit(-1)
                    
    @staticmethod
    def create_patch_contract_uses(_slither, patches, _name, _in_file):
        for contract in _slither.contracts_derived:
            if contract.name != _name:
                in_file_str = _slither.source_code[_in_file]
                # Check state variables of contract type
                # To-do: Deep-check aggregate types (struct and mapping)
                svs = contract.variables
                for sv in svs:
                    if (str(sv.type) == _name):
                        old_str_of_interest = in_file_str[contract.get_source_var_declaration(sv.name)['start']:(contract.get_source_var_declaration(sv.name)['start']+contract.get_source_var_declaration(sv.name)['length'])]
                        (new_str_of_interest, num_repl) = re.subn(_name, _name.capitalize(),old_str_of_interest, 1)
                        patches[_in_file].append({
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
                            patches[_in_file].append({
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
            
    @staticmethod
    def create_patch_modifier_definition(_slither, patches, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
        for contract in _slither.contracts_derived:
            if contract.name == _contract_name:
                for modifier in contract.modifiers:
                    if modifier.name == _name:
                        in_file_str = _slither.source_code[_in_file]
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                        m = re.match(r'(.*)'+"modifier"+r'(.*)'+_name, old_str_of_interest)
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_start+m.span()[1]]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"modifier"+r'(.*)'+_name, r'\1'+"modifier"+r'\2'+_name[0].lower()+_name[1:], old_str_of_interest, 1)
                        if num_repl != 0:
                            patches[_in_file].append({
                                "detector" : "naming-convention (modifier definition)",
                                "start" : _modify_loc_start,
                                "end" : _modify_loc_start+m.span()[1],
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            })
                        else:
                            print("Error: Could not find modifier?!")
                            sys.exit(-1)
                            
    @staticmethod
    def create_patch_modifier_uses(_slither, patches, _name, _contract_name, _in_file):
        for contract in _slither.contracts_derived:
            if contract.name == _contract_name:
                for function in contract.functions:
                    for m  in function.modifiers:
                        if (m.name == _name):
                            in_file_str = _slither.source_code[_in_file]
                            old_str_of_interest = in_file_str[int(function.parameters_src.split(':')[0]):int(function.returns_src.split(':')[0])]
                            (new_str_of_interest, num_repl) = re.subn(_name, _name[0].lower()+_name[1:],old_str_of_interest,1)
                            if num_repl != 0:
                                patches[_in_file].append({
                                    "detector" : "naming-convention (modifier uses)",
                                    "start" : int(function.parameters_src.split(':')[0]),
                                    "end" : int(function.returns_src.split(':')[0]),
                                    "old_string" : old_str_of_interest,
                                    "new_string" : new_str_of_interest
                                })
                            else:
                                print("Error: Could not find modifier name?!")
                                sys.exit(-1)
                                
    @staticmethod
    def create_patch_function_definition(_slither, patches, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
        # To-do Match on function full_name and not simply name to distinguish functions with same names but diff parameters
        for contract in _slither.contracts_derived:
            if contract.name == _contract_name:
                for function in contract.functions:
                    if function.name == _name:
                        in_file_str = _slither.source_code[_in_file]
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                        m = re.match(r'(.*)'+"function"+r'(.*)'+_name, old_str_of_interest)
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_start+m.span()[1]]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"function"+r'(.*)'+_name, r'\1'+"function"+r'\2'+_name[0].lower()+_name[1:], old_str_of_interest, 1)
                        if num_repl != 0:
                            patches[_in_file].append({
                                "detector" : "naming-convention (function definition)",
                                "start" : _modify_loc_start,
                                "end" : _modify_loc_start+m.span()[1],
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            })
                        else:
                            print("Error: Could not find function?!")
                            sys.exit(-1)
                            
    @staticmethod
    def create_patch_function_calls(_slither, patches, _name, _contract_name, _in_file):
        # To-do Match on function full_name and not simply name to distinguish functions with same names but diff parameters
        for contract in _slither.contracts_derived:
            for function in contract.functions:
                for node in function.nodes:
                    # To-do: Handle function calls of other contracts e.g. c.foo()
                    for call in node.internal_calls_as_expressions:
                        if (str(call.called) == _name):
                            in_file_str = _slither.source_code[_in_file]
                            old_str_of_interest = in_file_str[int(call.source_mapping['start']):int(call.source_mapping['start'])+int(call.source_mapping['length'])]
                            patches[_in_file].append({
                                "detector" : "naming-convention (function calls)",
                                "start" : call.source_mapping['start'],
                                "end" : int(call.source_mapping['start']) + int(call.source_mapping['length']),
                                "old_string" : old_str_of_interest,
                                "new_string" : old_str_of_interest[0].lower()+old_str_of_interest[1:]
                            })
                            
    @staticmethod
    def create_patch_event_definition(_slither, patches, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
        for contract in _slither.contracts_derived:
            if contract.name == _contract_name:
                for event in contract.events:
                    if event.full_name == _name:
                        event_name = _name.split('(')[0]
                        in_file_str = _slither.source_code[_in_file]
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"event"+r'(.*)'+event_name, r'\1'+"event"+r'\2'+event_name[0].capitalize()+event_name[1:], old_str_of_interest, 1)
                        if num_repl != 0:
                            patches[_in_file].append({
                                "detector" : "naming-convention (event definition)",
                                "start" : _modify_loc_start,
                                "end" : _modify_loc_end,
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            })
                        else:
                            print("Error: Could not find event?!")
                            sys.exit(-1)
                            
    @staticmethod
    def create_patch_event_calls(_slither, patches, _name, _contract_name, _in_file):
        # To-do Match on event _name and not simply event_name to distinguish events with same names but diff parameters    
        event_name = _name.split('(')[0]
        for contract in _slither.contracts_derived:
            if (contract.name == _contract_name):
                for function in contract.functions:
                    for node in function.nodes:
                        for call in node.internal_calls_as_expressions:
                            if (str(call.called) == event_name):
                                in_file_str = _slither.source_code[_in_file]
                                old_str_of_interest = in_file_str[int(call.source_mapping['start']):int(call.source_mapping['start'])+int(call.source_mapping['length'])]
                                patches[_in_file].append({
                                    "detector" : "naming-convention (event calls)",
                                    "start" : call.source_mapping['start'],
                                    "end" : int(call.source_mapping['start']) + int(call.source_mapping['length']),
                                    "old_string" : old_str_of_interest,
                                    "new_string" : old_str_of_interest[0].capitalize()+old_str_of_interest[1:]
                                })
                                
    @staticmethod
    def create_patch_parameter_declaration(_slither, patches, _name, _function_name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
        for contract in _slither.contracts_derived:
            if contract.name == _contract_name:
                for function in contract.functions:
                    if function.name == _function_name:
                        in_file_str = _slither.source_code[_in_file]
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                        if(_name[0] == '_'):
                            (new_str_of_interest, num_repl) = re.subn(r'(.*)'+_name+r'(.*)', r'\1'+_name[0]+_name[1].upper()+_name[2:]+r'\2', old_str_of_interest, 1)
                        else:
                            (new_str_of_interest, num_repl) = re.subn(r'(.*)'+_name+r'(.*)', r'\1'+'_'+_name[0].upper()+_name[1:]+r'\2', old_str_of_interest, 1)
                        if num_repl != 0:
                            patches[_in_file].append({
                                "detector" : "naming-convention (parameter declaration)",
                                "start" : _modify_loc_start,
                                "end" : _modify_loc_end,
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            })
                        else:
                            print("Error: Could not find parameter?!")
                            sys.exit(-1)

    @staticmethod                        
    def create_patch_parameter_uses(_slither, patches, _name, _function_name, _contract_name, _in_file):
        for contract in _slither.contracts_derived:
            if (contract.name == _contract_name):
                for function in contract.functions:
                    if (function.name == _function_name):
                        for node in function.nodes:
                            vars = node._expression_vars_written + node._expression_vars_read
                            for v in vars:
                                if isinstance(v, Identifier) and str(v) == _name and [str(lv) for lv in (node._local_vars_read+node._local_vars_written) if str(lv) == _name]:
                                    modify_loc_start = int(v.source_mapping['start'])
                                    modify_loc_end = int(v.source_mapping['start']) + int(v.source_mapping['length'])
                                    in_file_str = _slither.source_code[_in_file]
                                    old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                                    if(_name[0] == '_'):
                                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+_name+r'(.*)', r'\1'+_name[0]+_name[1].upper()+_name[2:]+r'\2', old_str_of_interest, 1)
                                    else:
                                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+_name+r'(.*)', r'\1'+'_'+_name[0].upper()+_name[1:]+r'\2', old_str_of_interest, 1)
                                    if num_repl != 0:
                                        patches[_in_file].append({
                                            "detector" : "naming-convention (parameter uses)",
                                            "start" : modify_loc_start,
                                            "end" : modify_loc_end,
                                            "old_string" : old_str_of_interest,
                                            "new_string" : new_str_of_interest
                                        })
                                    else:
                                        print("Error: Could not find parameter?!")
                                        sys.exit(-1)
                                        
    @staticmethod
    def create_patch_state_variable_declaration(_slither, patches, _target, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
        for contract in _slither.contracts_derived:
            if (contract.name == _contract_name):
                for var in contract.state_variables:
                    if (var.name == _name):
                        in_file_str = _slither.source_code[_in_file]
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                        m = re.search(_name, old_str_of_interest)
                        if (_target == "variable_constant"):
                            new_string = old_str_of_interest[m.span()[0]:m.span()[1]].upper()
                        else:
                            new_string = old_str_of_interest[m.span()[0]:m.span()[1]]
                            new_string = new_string[0].lower()+new_string[1:]
                        patches[_in_file].append({
                            "detector" : "naming-convention (state variable declaration)",
                            "start" : _modify_loc_start+m.span()[0],
                            "end" : _modify_loc_start+m.span()[1],
                            "old_string" : old_str_of_interest[m.span()[0]:m.span()[1]],
                            "new_string" : new_string 
                        })
                        
    @staticmethod
    def create_patch_state_variable_uses(_slither, patches, _target, _name, _contract_name, _in_file):
        # To-do: Check cross-contract state variable uses
        for contract in _slither.contracts_derived:
            if (contract.name == _contract_name):
                fms = contract.functions + contract.modifiers
                for fm in fms:
                    for node in fm.nodes:
                        vars = node._expression_vars_written + node._expression_vars_read
                        for v in vars:
                            if isinstance(v, Identifier) and str(v) == _name and [str(sv) for sv in (node._state_vars_read+node._state_vars_written) if str(sv) == _name]:
                                modify_loc_start = int(v.source_mapping['start'])
                                modify_loc_end = int(v.source_mapping['start']) + int(v.source_mapping['length'])
                                in_file_str = _slither.source_code[_in_file]
                                old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
                                if (_target == "variable_constant"):
                                    new_str_of_interest = old_str_of_interest.upper()
                                else:
                                    new_str_of_interest = old_str_of_interest
                                    new_str_of_interest = new_str_of_interest[0].lower()+new_str_of_interest[1:]
                                patches[_in_file].append({
                                    "detector" : "naming-convention (state variable uses)",
                                    "start" : modify_loc_start,
                                    "end" : modify_loc_end,
                                    "old_string" : old_str_of_interest,
                                    "new_string" : new_str_of_interest
                                })

    @staticmethod                                
    def create_patch_enum_definition(_slither, patches, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
        for contract in _slither.contracts_derived:
            if (contract.name == _contract_name):
                for enum in contract.enums:
                    if (enum.name == _name):
                        in_file_str = _slither.source_code[_in_file]
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"enum"+r'(.*)'+_name, r'\1'+"enum"+r'\2'+_name[0].capitalize()+_name[1:], old_str_of_interest, 1)
                        if num_repl != 0:
                            patches[_in_file].append({
                                "detector" : "naming-convention (enum definition)",
                                "start" : _modify_loc_start,
                                "end" : _modify_loc_end,
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            })
                        else:
                            print("Error: Could not find enum?!")
                            sys.exit(-1)
                            
    @staticmethod
    def create_patch_enum_uses(_slither, patches, _name, _contract_name, _in_file):
        for contract in _slither.contracts_derived:
            in_file_str = _slither.source_code[_in_file]
            # Check state variable declarations of enum type
            # To-do: Deep-check aggregate types (struct and mapping)
            svs = contract.variables
            for sv in svs:
                if (str(sv.type) == _contract_name + "." + _name):
                    old_str_of_interest = in_file_str[contract.get_source_var_declaration(sv.name)['start']:(contract.get_source_var_declaration(sv.name)['start']+contract.get_source_var_declaration(sv.name)['length'])]
                    (new_str_of_interest, num_repl) = re.subn(_name, _name.capitalize(),old_str_of_interest, 1)
                    patches[_in_file].append({
                        "detector" : "naming-convention (enum use)",
                        "start" : contract.get_source_var_declaration(sv.name)['start'],
                        "end" : contract.get_source_var_declaration(sv.name)['start'] + contract.get_source_var_declaration(sv.name)['length'],
                        "old_string" : old_str_of_interest,
                        "new_string" : new_str_of_interest
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
                        patches[_in_file].append({
                            "detector" : "naming-convention (enum use)",
                            "start" : fm.get_source_var_declaration(v.name)['start'],
                            "end" : fm.get_source_var_declaration(v.name)['start'] + fm.get_source_var_declaration(v.name)['length'],
                            "old_string" : old_str_of_interest,
                            "new_string" : new_str_of_interest
                        })
                # To-do Capture Enum uses such as "num = numbers.ONE;"
                # where numbers is not captured by slither as a variable/value on the RHS
            # To-do: Check any other place/way where enum type is used

    @staticmethod            
    def create_patch_struct_definition(_slither, patches, _name, _contract_name, _in_file, _modify_loc_start, _modify_loc_end):
        for contract in _slither.contracts_derived:
            if (contract.name == _contract_name):
                for struct in contract.structures:
                    if (struct.name == _name):
                        in_file_str = _slither.source_code[_in_file]
                        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
                        (new_str_of_interest, num_repl) = re.subn(r'(.*)'+"struct"+r'(.*)'+_name, r'\1'+"struct"+r'\2'+_name[0].capitalize()+_name[1:], old_str_of_interest, 1)
                        if num_repl != 0:
                            patches[_in_file].append({
                                "detector" : "naming-convention (struct definition)",
                                "start" : _modify_loc_start,
                                "end" : _modify_loc_end,
                                "old_string" : old_str_of_interest,
                                "new_string" : new_str_of_interest
                            })
                        else:
                            print("Error: Could not find struct?!")
                            sys.exit(-1)

    @staticmethod                            
    def create_patch_struct_uses(_slither, patches, _name, _contract_name, _in_file):
        for contract in _slither.contracts_derived:
            in_file_str = _slither.source_code[_in_file]
            # Check state variables of struct type
            # To-do: Deep-check aggregate types (struct and mapping)
            svs = contract.variables
            for sv in svs:
                if (str(sv.type) == _contract_name + "." + _name):
                    old_str_of_interest = in_file_str[contract.get_source_var_declaration(sv.name)['start']:(contract.get_source_var_declaration(sv.name)['start']+contract.get_source_var_declaration(sv.name)['length'])]
                    (new_str_of_interest, num_repl) = re.subn(_name, _name.capitalize(),old_str_of_interest, 1)
                    patches[_in_file].append({
                        "detector" : "naming-convention (struct use)",
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
                    if (str(v.type) == _contract_name + "." + _name):
                        old_str_of_interest = in_file_str[fm.get_source_var_declaration(v.name)['start']:(fm.get_source_var_declaration(v.name)['start']+fm.get_source_var_declaration(v.name)['length'])]
                        (new_str_of_interest, num_repl) = re.subn(_name, _name.capitalize(),old_str_of_interest, 1)
                        patches[_in_file].append({
                            "detector" : "naming-convention (struct use)",
                            "start" : fm.get_source_var_declaration(v.name)['start'],
                            "end" : fm.get_source_var_declaration(v.name)['start'] + fm.get_source_var_declaration(v.name)['length'],
                            "old_string" : old_str_of_interest,
                            "new_string" : new_str_of_interest
                        })
            # To-do: Check any other place/way where struct type is used (e.g. typecast)
