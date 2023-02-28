from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function


# pylint: disable=too-many-locals
def compare(v1: Contract, v2: Contract) -> dict:
    """
    Compares two versions of a contract. Most useful for upgradeable (logic) contracts,
    but does not require that Contract.is_upgradeable returns true for either contract.

    Args:
        v1: Original version of (upgradeable) contract
        v2: Updated version of (upgradeable) contract

    Returns: dict {
        "missing-vars-in-v2": list[Variable],
        "new-variables": list[Variable],
        "tainted-variables": list[Variable],
        "new-functions": list[Function],
        "modified-functions": list[Function],
        "tainted-functions": list[Function]
    }

    """

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
        "tainted-functions": [],
    }

    # Since this is not a detector, include any missing variables in the v2 contract
    if len(order_vars2) <= len(order_vars1):
        for variable in order_vars1:
            if variable.name not in [v.name for v in order_vars2]:
                results["missing-vars-in-v2"].append(variable)

    # Find all new and modified functions in the v2 contract
    new_modified_functions = []
    new_modified_function_vars = []
    for sig in func_sigs2:
        function = v2.get_function_from_signature(sig)
        orig_function = v1.get_function_from_signature(sig)
        if sig not in func_sigs1:
            new_modified_functions.append(function)
            results["new-functions"].append(function)
        elif is_function_modified(orig_function, function):
            new_modified_functions.append(function)
            results["modified-functions"].append(function)
        else:
            continue
        for var in function.state_variables_read + function.state_variables_written:
            if var not in new_modified_function_vars:
                new_modified_function_vars.append(var)

    # Find all unmodified functions that call a modified function or read/write the
    # same state variable(s) as a new/modified function, i.e., tainted functions
    for function in v2.functions:
        if function in new_modified_functions:
            continue
        modified_calls = [
            func for func in new_modified_functions if func in function.internal_calls
        ]
        tainted_vars = [
            var for var in new_modified_function_vars if var in function.variables_read_or_written
        ]
        if len(modified_calls) > 0 or len(tainted_vars) > 0:
            results["tainted-functions"].append(function)

    # Find all new or tainted variables, i.e., variables that are read or written by a new/modified function
    for idx, var in enumerate(order_vars2):
        read_by = v2.get_functions_reading_from_variable(var)
        written_by = v2.get_functions_writing_to_variable(var)
        if len(order_vars1) <= idx:
            results["new-variables"].append(var)
        elif any(func in read_by or func in written_by for func in new_modified_functions):
            results["tainted-variables"].append(var)

    return results


def is_function_modified(f1: Function, f2: Function) -> bool:
    """
    Compares two versions of a function, and returns True if the function has been modified.
    First checks whether the functions' content hashes are equal to quickly rule out identical functions.
    Walks the CFGs and compares IR operations if hashes differ to rule out false positives, i.e., from changed comments.

    Args:
        f1: Original version of the function
        f2: New version of the function

    Returns: True if the functions differ, otherwise False

    """
    # If the function content hashes are the same, no need to investigate the function further
    if f1.source_mapping.content_hash == f2.source_mapping.content_hash:
        return False
    # If the hashes differ, it is possible a change in a name or in a comment could be the only difference
    # So we need to resort to walking through the CFG and comparing the IR operations
    for i, node in enumerate(f2.nodes):
        for j, ir in enumerate(node.irs):
            if ir != f1.nodes[i].irs[j]:
                return True
    return False
