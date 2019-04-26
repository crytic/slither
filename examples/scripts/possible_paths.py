import os
import argparse
from slither import Slither


def resolve_function(contract_name, function_name):
    """
    Resolves a function instance, given a contract name and function.
    :param contract_name: The name of the contract the function is declared in.
    :param function_name: The name of the function to resolve.
    :return: Returns the resolved function, raises an exception otherwise.
    """
    # Obtain the target contract
    contract = slither.get_contract_from_name(contract_name)

    # Verify the contract was resolved successfully
    if contract is None:
        raise ValueError(f"Could not resolve target contract: {contract_name}")

    # Obtain the target function
    target_function = next((function for function in contract.functions if function.name == function_name), None)

    # Verify we have resolved the function specified.
    if target_function is None:
        raise ValueError(f"Could not resolve target function: {contract_name}.{function_name}")

    # Add the resolved function to the new list.
    return target_function


def resolve_functions(functions):
    """
    Resolves the provided function descriptors.
    :param functions: A list of tuples (contract_name, function_name) or str (of form "ContractName.FunctionName")
    to resolve into function objects.
    :return: Returns a list of resolved functions.
    """
    # Create the resolved list.
    resolved = []

    # Verify that the provided argument is a list.
    if not isinstance(functions, list):
        raise ValueError("Provided functions to resolve must be a list type.")

    # Loop for each item in the list.
    for item in functions:
        if isinstance(item, str):
            # If the item is a single string, we assume it is of form 'ContractName.FunctionName'.
            parts = item.split('.')
            if len(parts) < 2:
                raise ValueError("Provided string descriptor must be of form 'ContractName.FunctionName'")
            resolved.append(resolve_function(parts[0], parts[1]))
        elif isinstance(item, tuple):
            # If the item is a tuple, it should be a 2-tuple providing contract and function names.
            if len(item) != 2:
                raise ValueError("Provided tuple descriptor must provide a contract and function name.")
            resolved.append(resolve_function(item[0], item[1]))
        else:
            raise ValueError(f"Unexpected function descriptor type to resolve in list: {type(item)}")

    # Return the resolved list.
    return resolved


def all_function_definitions(function):
    """
    Obtains a list of representing this function and any base definitions
    :param function: The function to obtain all definitions at and beneath.
    :return: Returns a list composed of the provided function definition and any base definitions.
    """
    return [function] + [f for c in function.contract.inheritance
                         for f in c.functions_and_modifiers_not_inherited
                         if f.full_name == function.full_name]


def __find_target_paths(target_function, current_path=[]):

    # Create our results list
    results = set()

    # Add our current function to the path.
    current_path = [target_function] + current_path

    # Obtain this target function and any base definitions.
    all_target_functions = set(all_function_definitions(target_function))

    # Look through all functions
    for contract in slither.contracts:
        for function in contract.functions_and_modifiers_not_inherited:

            # If the function is already in our path, skip it.
            if function in current_path:
                continue

            # Find all function calls in this function (except for low level)
            called_functions = [f for (_, f) in function.high_level_calls + function.library_calls]
            called_functions += function.internal_calls
            called_functions = set(called_functions)

            # If any of our target functions are reachable from this function, it's a result.
            if all_target_functions.intersection(called_functions):
                path_results = __find_target_paths(function, current_path.copy())
                if path_results:
                    results = results.union(path_results)

    # If this path is external accessible from this point, we add the current path to the list.
    if target_function.visibility in ['public', 'external'] and len(current_path) > 1:
        results.add(tuple(current_path))

    return results


def find_target_paths(target_functions):
    """
    Obtains all functions which can lead to any of the target functions being called.
    :param target_functions: The functions we are interested in reaching.
    :return: Returns a list of all functions which can reach any of the target_functions.
    """
    # Create our results list
    results = set()

    # Loop for each target function
    for target_function in target_functions:
        results = results.union(__find_target_paths(target_function))

    return results


def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(description='PossiblePaths',
                                     usage='possible_paths.py [--is-truffle] filename [contract.function targets]')

    parser.add_argument('--is-truffle',
                        help='Indicates the filename refers to a truffle directory path.',
                        action='store_true',
                        default=False)

    parser.add_argument('filename',
                        help='The filename of the contract or truffle directory to analyze.')

    parser.add_argument('targets', nargs='+')

    return parser.parse_args()


# ------------------------------
# PossiblePaths.py
#       Usage: python3 possible_paths.py [--is-truffle] filename targets
#       Example: python3 possible_paths.py contract.sol contract1.function1 contract2.function2 contract3.function3
# ------------------------------
# Parse all arguments
args = parse_args()

# If this is a truffle project, verify we have a valid build directory.
if args.is_truffle:
    cwd = os.path.abspath(args.filename)
    build_dir = os.path.join(cwd, "build", "contracts")
    if not os.path.exists(build_dir):
        raise FileNotFoundError(f"Could not find truffle build directory at '{build_dir}'")

# Perform slither analysis on the given filename
slither = Slither(args.filename, is_truffle=args.is_truffle)

targets = resolve_functions(args.targets)

# Print out all target functions.
print(f"Target functions:")
for target in targets:
    print(f"-{target.contract.name}.{target.full_name}")
print("\n")

# Obtain all paths which reach the target functions.
reaching_paths = find_target_paths(targets)
reaching_functions = set([y for x in reaching_paths for y in x if y not in targets])

# Print out all function names which can reach the targets.
print(f"The following functions reach the specified targets:")
for function_desc in sorted([f"{f.canonical_name}" for f in reaching_functions]):
    print(f"-{function_desc}")
print("\n")

# Format all function paths.
reaching_paths_str = [' -> '.join([f"{f.canonical_name}" for f in reaching_path]) for reaching_path in reaching_paths]

# Print a sorted list of all function paths which can reach the targets.
print(f"The following paths reach the specified targets:")
for reaching_path in sorted(reaching_paths_str):
    print(f"{reaching_path}\n")
