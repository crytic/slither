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

    if len(order_vars2) <= len(order_vars1):
        for variable in order_vars1:
            if variable.name not in [v.name for v in order_vars2]:
                results["missing-vars-in-v2"].append(variable)

    new_modified_functions = []
    for sig in func_sigs2:
        function = v2.get_function_from_signature(sig)
        if sig not in func_sigs1:
            new_modified_functions.append(function)
            results["new-functions"].append(function)
        else:
            orig_function = v1.get_function_from_signature(sig)
            if function
