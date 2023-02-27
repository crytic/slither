from slither.core.declarations.contract import Contract


def compare(v1: Contract, v2: Contract):
    order_vars1 = [v for v in v1.state_variables if not v.is_constant and not v.is_immutable]
    order_vars2 = [v for v in v2.state_variables if not v.is_constant and not v.is_immutable]
    func_sigs1 = [function.solidity_signature for function in v1.functions]
    func_sigs2 = [function.solidity_signature for function in v2.functions]

    results = {
        "missing-vars-in-v2": [],
        "new-variables": [],
        "tainted-variables": [],
        "new-functions": [],
        "modified-functions": [],
        "tainted-functions": []
    }

    # Since this is not a detector, include any missing variables in the v2 contract
    if len(order_vars2) <= len(order_vars1):
        for variable in order_vars1:
            if variable.name not in [v.name for v in order_vars2]:
                results["missing-vars-in-v2"].append(variable)

    # Find all new and modified functions in the v2 contract
    new_modified_functions = []
    for sig in func_sigs2:
        function = v2.get_function_from_signature(sig)
        if sig not in func_sigs1:
            new_modified_functions.append(function)
            results["new-functions"].append(function)
        else:
            orig_function = v1.get_function_from_signature(sig)
            # If the function content hashes are the same, no need to investigate the function further
            if function.source_mapping.content_hash != orig_function.source_mapping.content_hash:
                # If the hashes differ, it is possible a change in a name or in a comment could be the only difference
                # So we need to resort to walking through the CFG and comparing the IR operations
                for i, node in enumerate(function.nodes):
                    if function in new_modified_functions:
                        break
                    for j, ir in enumerate(node.irs):
                        if ir != orig_function.nodes[i].irs[j]:
                            new_modified_functions.append(function)
                            results["modified-functions"].append(function)

    # Find all unmodified functions that call a modified function, i.e., tainted functions
    for function in v2.functions:
        if function in new_modified_functions:
            continue
        modified_calls = [funct for func in new_modified_functions if func in function.internal_calls]
        if len(modified_calls) > 0:
            results["tainted-functions"].append(function)

    # Find all new or tainted variables, i.e., variables that are read or written by a new/modified function
    for idx, var in enumerate(order_vars2):
        read_by = v2.get_functions_reading_from_variable(var)
        written_by = v2.get_functions_writing_to_variable(var)
        if len(order_vars1) <= idx:
            results["new-variables"].append(var)
        elif any([func in read_by or func in written_by for func in new_modified_functions]):
            results["tainted-variables"].append(var)
